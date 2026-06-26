# electronics demo (github-io)

GitHub Pages–style showcase for the **`cadbuildr.electronics`** library. It runs
Python in the browser (Pyodide + `cadbuildr.foundation`), builds PCB examples,
posts the DAG to **kernel-api**, and renders the populated boards in R3F via
[`@cadbuildr/sdk-react`](https://www.npmjs.com/package/@cadbuildr/sdk-react).

## Run it

```bash
# 1) build the PCB wheel for micropip (the dev server serves ../dist/*.whl)
uv build

# 2) JS deps + dev server
cd github-io
npm install
npm run dev
```

Open the URL Vite prints (default **http://localhost:3008**). Kernel requests go
to **`https://kernel-api.cadbuildr.com`** by default; override with
`VITE_KERNEL_API_BASE_URL` (e.g. a local kernel-api). See `.env.example` for all
options.

## Auth

The demo uses `CadbuildrProvider`. By default it uses the **keyId browser flow**
(`VITE_CADBUILDR_SDK_KEY_ID`, origin-locked, no secret in the bundle) to mint a
short-lived token from the hub. For local dev against an open-mode kernel-api you
can instead set `VITE_CADBUILDR_SESSION_TOKEN` to any `cbv1.*` string.

## What's in the demo

- **Boards** tab — Arduino Uno, Arduino Nano, Raspberry Pi, Raspberry Pi Pico,
  ESP32 DevKitC. Each renders bare (drilled board) and reveals its components via
  the assembly tree.
- **Components** tab — individual parts (resistor, LED, headers, ICs, connectors,
  …) shown solo from a dropdown.

## Deploy (GitHub Pages)

`.github/workflows/deploy-pages.yml` builds the wheel, stages it under
`github-io/public/local-pcb/`, Vite-builds with `VITE_APP_BASE_PATH=/electronics/`,
and deploys to Pages. Set a repo secret `CADBUILDR_SDK_KEY_ID` to use a dedicated
publishable key (the build falls back to the bundled origin-locked demo key).
