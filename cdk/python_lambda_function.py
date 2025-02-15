import os
import platform
import shlex
import shutil
import subprocess
import sys
from typing import NamedTuple

import jsii
from aws_cdk import (
    AssetHashType,
    BundlingOptions,
    DockerImage,
    DockerVolume,
    ILocalBundling,
    aws_ecr_assets,
    aws_lambda,
)
from constructs import Construct


class _Architecture(NamedTuple):
    lambda_architecture: aws_lambda.Architecture
    platform_machine: str
    docker_architecture: str
    ecr_platform: aws_ecr_assets.Platform


_ARCHITECTURES = {
    aws_lambda.Architecture.X86_64.name: _Architecture(
        aws_lambda.Architecture.X86_64, "x86_64", "amd64", aws_ecr_assets.Platform.LINUX_AMD64
    ),
    aws_lambda.Architecture.ARM_64.name: _Architecture(
        aws_lambda.Architecture.ARM_64, "aarch64", "arm64", aws_ecr_assets.Platform.LINUX_ARM64
    ),
}


def python_version_from_runtime(runtime: aws_lambda.Runtime) -> str:
    return runtime.name.removeprefix("python")


DEFAULT_LAMBDA_RUNTIME = aws_lambda.Runtime.PYTHON_3_11
DEFAULT_PYTHON_VERSION = python_version_from_runtime(DEFAULT_LAMBDA_RUNTIME)
DEFAULT_LAMBDA_ARCHITECTURE = aws_lambda.Architecture.X86_64
DEFAULT_ARCHITECTURE = _ARCHITECTURES[DEFAULT_LAMBDA_ARCHITECTURE.name]

# The Docker image used for bundling, needs to have the same Python version and platform as the
# Lambda function. We currently provide the image with sha to ensure the correct platform is used
# because the platform=... value we provide is ignored by CDK: https://github.com/aws/aws-cdk/issues/30239
# When this is fixed, we can use a tag like uv:python{PYTHON_VERSION}-... instead.
#
# To find a tag:
# https://github.com/astral-sh/uv/pkgs/container/uv/320975267?tag=python3.11-bookworm-slim -> OS/Arch -> pick same as above
DEFAULT_BUNDLING_DOCKER_IMAGE = "ghcr.io/astral-sh/uv:0.5.13-python3.11-bookworm-slim@sha256:dc0c70e35f899c69cfe3674afac6186b210373d19d7ed77fd8ab1bdc45f8bf15"


def log(package_name, *message):
    print(f"[{package_name}]", *message)


def run_command(args, env=None):
    result = subprocess.run(args, capture_output=True, env=env or {})
    if result.returncode != 0:
        raise RuntimeError(result.stderr)
    return result


def build_asset_command_and_env(
    package_name: str,
    output_path: str,
    architecture: _Architecture,
    python_version: str,
) -> tuple[list[str], dict[str, str]]:
    # Always use the same path per package to ensure that paths in the output are stable
    tmp_path = os.path.join("/tmp", f"uv-demo-{package_name}-build")

    commands = [
        # Ensure we are on the correct architecture
        '[ "$(uname -m)" = {architecture} ]'.format(architecture=architecture.platform_machine),
        # Create a virtual environment with the package's dependencies
        "uv sync --package {package_name} --frozen --no-dev --no-editable --compile-bytecode --python {python_version}".format(
            package_name=shlex.quote(package_name), python_version=python_version
        ),
        # Copy the virtual environment's site packages to the output path
        "cp -r {src} {dest}".format(
            src=os.path.join(tmp_path, "lib", f"python{python_version}", "site-packages", "."),
            dest=os.path.join(output_path.rstrip("/"), ""),
        ),
    ]
    command = ["bash", "-c", " && ".join(commands)]

    env = {
        "UV_PROJECT_ENVIRONMENT": tmp_path,
        "UV_NO_INSTALLER_METADATA": "1",  # don't write uv data that includes timestamps to dist-info directories
        "UV_LINK_MODE": "copy",
        "SOURCE_DATE_EPOCH": "444444444",  # for reproducible bytecode, 0 is not allowed because zip requires timestamps after 1980
    }
    return command, env


def validate_python_lambda_args(
    runtime: aws_lambda.Runtime,
    architecture: aws_lambda.Architecture,
    bundling_docker_image: str | None,
    package_name: str,
):
    def ensure_value(argument_name, actual, expected):
        assert (
            actual.name == expected.name
        ), f"Only {argument_name}={expected.name} is supported with the default bundling image, got {actual.name}"

    lambda_architecture = architecture

    if bundling_docker_image is None:
        # Use the default image and check if the other args match because the image has a specific platform

        ensure_value("runtime", runtime, DEFAULT_LAMBDA_RUNTIME)
        runtime = DEFAULT_LAMBDA_RUNTIME
        python_version = DEFAULT_PYTHON_VERSION
        ensure_value("architecture", lambda_architecture, DEFAULT_LAMBDA_ARCHITECTURE)
        architecture = DEFAULT_ARCHITECTURE
        bundling_docker_image = DEFAULT_BUNDLING_DOCKER_IMAGE
    else:
        # Use the provided image and don't check the other args
        if "@" not in bundling_docker_image:
            log(
                package_name,
                "Docker image was not provided with hash, incorrect platform may be used...",
            )
        architecture = _ARCHITECTURES[lambda_architecture.name]
        python_version = python_version_from_runtime(runtime)

    return runtime, architecture, bundling_docker_image, python_version


def python_lambda_code(
    path: str,
    package_name: str,
    handler: str | None,
    architecture: _Architecture,
    bundling_docker_image: str,
    python_version: str,
) -> aws_lambda.AssetCode:
    module_name = package_name.replace("-", "_")
    handler = handler or f"{module_name}.lambda_function.lambda_handler"

    try:
        cache_dir = run_command(["uv", "cache", "dir"], env=os.environ).stdout.decode().strip()
        volumes = [DockerVolume(container_path="/opt/uv-cache", host_path=cache_dir)]
        log(package_name, "found uv cache dir", cache_dir)
    except (RuntimeError, FileNotFoundError):
        log(package_name, "Local uv could not be found, not using cache dir mount...")
        volumes = None

    command, env = build_asset_command_and_env(
        package_name,
        output_path="/asset-output",
        architecture=architecture,
        python_version=python_version,
    )

    return aws_lambda.Code.from_asset(
        path,
        asset_hash_type=AssetHashType.OUTPUT,  # decide hash based on output (default: based on input)
        bundling=BundlingOptions(
            image=DockerImage.from_registry(bundling_docker_image),
            environment={
                **env,
                "UV_CACHE_DIR": "/opt/uv-cache/",
            },
            volumes=volumes,
            command=command,
            # The platform we provide here is ignored by CDK https://github.com/aws/aws-cdk/issues/30239
            # See BUNDLING_DOCKER_IMAGE comment on top
            platform=architecture.docker_architecture,
            local=_UvLocalBundling(package_name, architecture, python_version),
        ),
    )


class PythonLambdaFunction(aws_lambda.Function):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        package_name: str,
        path: str,
        handler: str | None = None,
        runtime: aws_lambda.Runtime = DEFAULT_LAMBDA_RUNTIME,
        architecture: aws_lambda.Architecture = DEFAULT_LAMBDA_ARCHITECTURE,
        bundling_docker_image: str | None = None,
        **kwargs,
    ):
        runtime, architecture, bundling_docker_image, python_version = validate_python_lambda_args(
            runtime, architecture, bundling_docker_image, package_name
        )
        super().__init__(
            scope,
            construct_id,
            code=python_lambda_code(
                path,
                package_name,
                handler=handler,
                architecture=architecture,
                bundling_docker_image=bundling_docker_image,
                python_version=python_version,
            ),
            handler=handler,
            runtime=runtime,
            architecture=architecture.lambda_architecture,
            **kwargs,
        )


@jsii.implements(ILocalBundling)
class _UvLocalBundling:
    def __init__(self, package_name: str, architecture: _Architecture, python_version: str) -> None:
        self.package_name = package_name
        self.architecture = architecture
        self.python_version = python_version
        super().__init__()

    def try_bundle(self, output_dir: str, *args, **kwargs) -> bool:
        # Only allow bundling on Linux with the same platform as the Lambda function
        if sys.platform != "linux" or platform.machine() != self.architecture.platform_machine:
            log(
                self.package_name,
                f"Local bundling is only supported on {self.architecture.platform_machine} Linux, using Docker bundling instead...",
            )
            return False

        # Only allow local bundling if /tmp is not a symlink for reproducibility
        if os.path.islink("/tmp"):
            log(
                self.package_name,
                "Local bundling is not supported when /tmp is a symlink, using Docker bundling instead...",
            )
            return False

        try:
            command, env = build_asset_command_and_env(
                self.package_name,
                output_path=output_dir,
                architecture=self.architecture,
                python_version=self.python_version,
            )
            run_command(command, env={**os.environ, **env})
        except RuntimeError as e:
            log(self.package_name, "Local bundling failed:", e)
            return False

        return True


def python_docker_lambda_code(
    scope: Construct,
    package_name: str,
    path: str,
    dockerfile: str,
    handler: str | None,
    architecture: _Architecture,
    bundling_docker_image: str | None,
    python_version: str,
) -> aws_lambda.AssetImageCode:
    lambda_code = python_lambda_code(
        path, package_name, handler, architecture, bundling_docker_image, python_version
    )
    asset_scope = Construct(scope, f"{package_name}Asset")
    asset = lambda_code.bind(asset_scope)
    asset_dir = os.path.join(
        "cdk.out", f"asset.{asset.s3_location.object_key.removesuffix('.zip')}"
    )
    if not os.path.exists(asset_dir):
        print("Asset directory does not exist. This should only happen on CDK destroy")
        os.makedirs(asset_dir)

    work_dir = asset_dir + "-docker"
    shutil.rmtree(work_dir, ignore_errors=True)
    shutil.copytree(asset_dir, work_dir)

    shutil.copy(dockerfile, work_dir)
    with open(os.path.join(work_dir, ".dockerignore"), "w") as f:
        f.write("Dockerfile\n.dockerignore\n")

    return aws_lambda.Code.from_asset_image(
        cmd=[handler],
        directory=work_dir,
        asset_name=package_name,
        build_args={"PYTHON_VERSION": python_version},
        platform=architecture.ecr_platform,
    )


class PythonDockerLambdaFunction(aws_lambda.Function):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        package_name: str,
        path: str,
        dockerfile: str,
        handler: str | None = None,
        runtime: aws_lambda.Runtime = DEFAULT_LAMBDA_RUNTIME,
        architecture: aws_lambda.Architecture = DEFAULT_LAMBDA_ARCHITECTURE,
        bundling_docker_image: str | None = None,
        **kwargs,
    ):
        runtime, architecture, bundling_docker_image, python_version = validate_python_lambda_args(
            runtime, architecture, bundling_docker_image, package_name
        )

        super().__init__(
            scope,
            construct_id,
            runtime=aws_lambda.Runtime.FROM_IMAGE,
            handler=aws_lambda.Handler.FROM_IMAGE,
            code=python_docker_lambda_code(
                scope,
                package_name,
                path=path,
                dockerfile=dockerfile,
                handler=handler,
                architecture=architecture,
                bundling_docker_image=bundling_docker_image,
                python_version=python_version,
            ),
            **kwargs,
        )
