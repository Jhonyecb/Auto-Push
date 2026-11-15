#!/usr/bin/env python3
"""
Script de automação Git/GitHub.
Inicializa repositório, adiciona arquivos, cria commit, conecta ao remoto e faz push.
Opcionalmente cria o repositório no GitHub via API antes de tudo.
"""

import os
import subprocess
import sys
import requests  # necessário apenas se USE_GITHUB_API=True (pip install requests)

# ==========================================================
# CONFIGURAÇÕES — edite estes valores conforme sua necessidade
# ==========================================================
FOLDER_PATH = r"C:\Users\User\Documents\Auto Push"        # pasta que será versionada
REMOTE_URL = "https://github.com/Jhonyecb/Auto-Push"  # URL do repositório remoto
COMMIT_MESSAGE = "Commit automático"
BRANCH = "main"

# Configurações opcionais para criação automática do repositório via API
USE_GITHUB_API = False              # True para criar o repo automaticamente
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")  # token de autenticação (variável de ambiente recomendada)
GITHUB_USERNAME = "usuario"
REPO_NAME = "repo"
REPO_PRIVATE = True


def run_git_command(command, cwd):
    """Executa um comando git e trata erros de forma centralizada."""
    result = subprocess.run(
        command, cwd=cwd, capture_output=True, text=True, shell=False
    )
    if result.returncode != 0:
        print(f"Erro ao executar: {' '.join(command)}")
        print(result.stderr.strip())
        return False, result.stderr
    return True, result.stdout


def create_github_repo():
    """Cria o repositório no GitHub via API, caso ainda não exista."""
    if not GITHUB_TOKEN:
        print("Token do GitHub não configurado. Defina GITHUB_TOKEN.")
        sys.exit(1)

    url = "https://api.github.com/user/repos"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }
    payload = {"name": REPO_NAME, "private": REPO_PRIVATE}

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 201:
        print(f"Repositório '{REPO_NAME}' criado com sucesso no GitHub.")
    elif response.status_code == 422:
        # 422 geralmente indica que o repositório já existe
        print("Repositório já existe no GitHub. Prosseguindo.")
    else:
        print(f"Falha ao criar repositório: {response.status_code} - {response.text}")
        sys.exit(1)


def ensure_git_initialized(folder):
    """Inicializa o repositório git se ainda não existir um .git na pasta."""
    git_dir = os.path.join(folder, ".git")
    if os.path.isdir(git_dir):
        print("Repositório já inicializado. Pulando 'git init'.")
        return True

    ok, _ = run_git_command(["git", "init"], cwd=folder)
    if ok:
        print("Repositório git inicializado.")
    return ok


def ensure_remote(folder, remote_url):
    """Configura o remoto 'origin'. Se já existir, atualiza a URL."""
    ok, out = run_git_command(["git", "remote"], cwd=folder)
    if not ok:
        return False

    if "origin" in out.split():
        run_git_command(["git", "remote", "set-url", "origin", remote_url], cwd=folder)
        print("Remoto 'origin' atualizado.")
    else:
        ok, _ = run_git_command(["git", "remote", "add", "origin", remote_url], cwd=folder)
        if ok:
            print("Remoto 'origin' adicionado.")
    return True


def commit_and_push(folder, message, branch):
    """Adiciona arquivos, cria commit e faz push, tratando erros comuns."""

    # Adiciona todos os arquivos da pasta
    ok, _ = run_git_command(["git", "add", "."], cwd=folder)
    if not ok:
        print("Falha ao adicionar arquivos.")
        return False

    # Verifica se há algo para commitar (evita erro de 'nothing to commit')
    ok, status_out = run_git_command(["git", "status", "--porcelain"], cwd=folder)
    if not status_out.strip():
        print("Nenhuma alteração para commitar.")
    else:
        ok, err = run_git_command(["git", "commit", "-m", message], cwd=folder)
        if not ok:
            print("Falha ao criar commit.")
            print(err)
            return False
        print("Commit criado com sucesso.")

    # Garante que a branch local tenha o nome correto
    run_git_command(["git", "branch", "-M", branch], cwd=folder)

    # Push com tratamento de erros de autenticação e conflitos
    ok, err = run_git_command(["git", "push", "-u", "origin", branch], cwd=folder)
    if not ok:
        if "Authentication failed" in err or "could not read Username" in err:
            print("Falha de autenticação. Verifique seu token/credenciais do GitHub.")
        elif "rejected" in err or "non-fast-forward" in err:
            print("Push rejeitado por conflito. Execute 'git pull --rebase' antes de tentar novamente.")
        else:
            print("Falha desconhecida no push.")
            print(err)
        return False

    print("Push realizado com sucesso.")
    return True


def main():
    if not os.path.isdir(FOLDER_PATH):
        print(f"Pasta não encontrada: {FOLDER_PATH}")
        sys.exit(1)

    if USE_GITHUB_API:
        create_github_repo()

    if not ensure_git_initialized(FOLDER_PATH):
        sys.exit(1)

    if not ensure_remote(FOLDER_PATH, REMOTE_URL):
        sys.exit(1)

    commit_and_push(FOLDER_PATH, COMMIT_MESSAGE, BRANCH)


if __name__ == "__main__":
    main()