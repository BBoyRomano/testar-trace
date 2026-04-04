# TbUIS app artifact manifest

The TbUIS application is executed from its hosted deployment during TESTAR runs.

## Hosted target

- `https://projects.kiv.zcu.cz/tbuis/web/page/uis`

## Repository policy

- Large binary application artifacts (for example WAR files) are not stored in this repository by default.
- If a local binary becomes necessary for a specific experiment, store retrieval/build instructions and checksum metadata here instead of committing the binary itself.
