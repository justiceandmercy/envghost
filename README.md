# envghost

Find environment variables that are declared but never referenced, and references that have no declaration.

## Features

- Scans common `.env` files and source files in one pass.
- Detects references from Python, JavaScript, TypeScript, Go, Ruby, shell, and more.
- Reports unused declarations and missing declarations.
- Supports text and JSON output.
- Exits nonzero for CI when requested.

## Install

Clone the repository and run it as a module:

```sh
git clone https://example.com/envghost.git
cd envghost
python -m envghost --help
```

No third-party dependencies are required.

## Usage

Scan the current directory:

```sh
python -m envghost
```

Scan another project:

```sh
python -m envghost /path/to/project
```

Use a custom env file:

```sh
python -m envghost --env-file .env --env-file .env.local
```

Emit JSON:

```sh
python -m envghost --format json
```

Do not fail CI for missing variables:

```sh
python -m envghost --fail-on unused
```

## License

MIT