{
  description = "Development environment for Ansible collection work (uv-managed)";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
      in
      {
        devShells.default = pkgs.mkShell {
          name = "ansible-kanidm";

          packages = with pkgs.python313Packages; [
            python
            uv
            ruff
            mypy
            pytest
            yamllint
            tox
          ];

          shellHook = ''
            echo "Setting up Ansible collection dev environment (uv-managed)..."

            # Create a uv-managed venv if it doesn't exist
            if [ ! -d .venv ]; then
              uv venv .venv
            fi
            source .venv/bin/activate

            uv sync

            echo "Ready. Tools available:"
            echo "  ansible-creator, ansible-lint, ansible-navigator, pytest-ansible, molecule, tox-ansible (via ansible-dev-tools)"
            echo "  antsibull-docs, pytest, mypy, ruff, yamllint, tox"
          '';
        };
      });
}