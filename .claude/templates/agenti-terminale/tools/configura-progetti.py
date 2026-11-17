"""Riapplica i soli progetti autorizzati della macchina a una radice nuova.

Registro privato, nessun token. Richiede Python 3.11+ solo se il registro esiste.
Le definizioni MCP rimangono nel progetto; non si clonano account o credenziali.
"""
import argparse
import json
import os
import tempfile
import tomllib
from datetime import UTC, datetime
from pathlib import Path


def key(value):
    return value.replace('\\', '/').rstrip('/').casefold()


def prepare(registry, agent, accounts, user_profile, allow_missing=False):
    data = json.loads(Path(registry).read_text(encoding='utf-8-sig'))
    if data.get('schema') != 'agent-projects-0.1' or not isinstance(data.get('projects'), list):
        raise ValueError('Registro dei progetti non valido.')
    projects = []
    for item in data['projects']:
        path = Path(item['path'])
        names = item['mcp_servers']
        if (not path.is_absolute() or not path.is_dir() or not isinstance(names, list)
                or not names or any(not isinstance(n, str) or not n for n in names)):
            raise ValueError('Progetto o elenco dei server non valido.')
        path = path.resolve()
        if key(str(path)) in {key(str(p)) for p in projects}:
            raise ValueError('Progetto duplicato nel registro.')
        if agent == 'claude':
            config = json.loads((path / '.mcp.json').read_text(encoding='utf-8-sig'))
            configured = config.get('mcpServers', {})
            settings = json.loads((path / '.claude/settings.local.json').read_text(encoding='utf-8-sig'))
            enabled = settings.get('enabledMcpjsonServers', [])
            if any(name not in enabled for name in names) and settings.get('enableAllProjectMcpServers') is not True:
                raise ValueError('Server non abilitato nelle impostazioni locali del progetto.')
        else:
            config = tomllib.loads((path / '.codex/config.toml').read_text(encoding='utf-8-sig'))
            configured = config.get('mcp_servers', {})
        if any(name not in configured or configured[name].get('enabled') is False for name in names):
            raise ValueError('Definizione MCP di progetto mancante o disabilitata.')
        projects.append(path)
    if any(type(n) is not int or not 1 <= n <= 99 for n in accounts):
        raise ValueError('Numero account non valido.')
    changes = []
    for number in sorted(set(accounts)):
        root = Path(user_profile) / f'.{agent}-account{number}'
        if not root.is_dir():
            if allow_missing:
                continue
            raise ValueError('Installare prima la radice account.')
        if agent == 'claude':
            continue  # MCP e abilitazioni sono condivisi nel progetto.
        target = root / 'config.toml'
        before = target.read_bytes()
        parsed = tomllib.loads(before.decode('utf-8-sig'))
        after = before
        newline = '\r\n' if b'\r\n' in before else '\n'
        for project in projects:
            matches = [value for path, value in parsed.get('projects', {}).items()
                       if key(path) == key(str(project))]
            if matches:
                if len(matches) != 1 or matches[0].get('trust_level') != 'trusted':
                    raise ValueError('Fiducia esistente divergente: non sovrascritta.')
                continue
            addition = ('\n# Progetto autorizzato dal registro privato della macchina.\n[projects.'
                        + json.dumps(str(project), ensure_ascii=False) + ']\ntrust_level = "trusted"\n')
            after += addition.replace('\n', newline).encode()
        tomllib.loads(after.decode('utf-8-sig'))
        if after != before:
            changes.append((target, before, after))
    return changes, len(projects)


def apply(changes):
    # Tutto il piano viene validato prima della prima scrittura.
    stamp = datetime.now(UTC).strftime('%Y%m%dT%H%M%S%fZ')
    for target, before, _ in changes:
        if target.read_bytes() != before:
            raise ValueError('Configurazione cambiata durante la verifica.')
        with target.with_name('config.progetti-' + stamp + '.bak').open('xb') as stream:
            stream.write(before)
    for target, before, after in changes:
        if target.read_bytes() != before:
            raise ValueError('Configurazione cambiata durante la scrittura.')
        handle, temporary = tempfile.mkstemp(prefix='.progetti-', dir=target.parent)
        try:
            with os.fdopen(handle, 'wb') as stream:
                stream.write(after)
            os.replace(temporary, target)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registry', required=True, type=Path)
    parser.add_argument('--agent', required=True, choices=['claude', 'codex'])
    parser.add_argument('--account', required=True, type=int, nargs='+')
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    try:
        changes, projects = prepare(args.registry, args.agent, args.account, os.environ['USERPROFILE'], args.verify)
        if not args.verify:
            apply(changes)
        print(f'Progetti MCP: {projects}; account selezionati: {len(set(args.account))}; '
              f'configurazioni {"da aggiornare" if args.verify else "aggiornate"}: {len(changes)}. '
              'Credenziali non lette o copiate.')
        missing = sum(not (Path(os.environ['USERPROFILE']) / f'.{args.agent}-account{n}').is_dir()
                      for n in set(args.account))
        if missing:
            print(f'Radici ancora da installare: {missing}; la fiducia verrà applicata dopo la creazione.')
        return 0
    except (OSError, ValueError, KeyError, TypeError):
        print('Registro progetti, configurazione MCP o fiducia non validi. Nessuna credenziale copiata.')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
