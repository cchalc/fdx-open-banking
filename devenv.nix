{ pkgs, ... }: {
  # Disable cachix binary cache management — requires trusted-user in nix.conf.
  cachix.enable = false;

  languages.python.enable = true;
  languages.python.package = pkgs.python311;
  languages.python.uv.enable = true;

  # podman (mock servers) and just are expected on PATH from the host profile.

  enterShell = ''
    # One shared venv for every wt worktree (see architecture.md).
    export UV_PROJECT_ENVIRONMENT="$HOME/.virtualenvs/fdx-open-banking"
    if [ ! -d "$UV_PROJECT_ENVIRONMENT" ]; then
      uv sync
    fi
  '';
}
