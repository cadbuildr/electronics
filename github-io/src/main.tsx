import React from "react";
import ReactDOM from "react-dom/client";
import { type KernelDag } from "@cadbuildr/cad-kernel-r3f";
import {
  initializeCadPyodideRuntime,
  runCadPythonCode,
  type PyodideLike,
} from "@cadbuildr/cad-pyodide-runtime";
import { CadbuildrProvider, CadbuildrViewer } from "@cadbuildr/sdk-react";

import { resolveKernelApiBaseUrl } from "./kernelApiEnv";
import { LOCAL_PCB_URL_SEGMENT, LOCAL_PCB_WHEEL_FILE } from "./pcbLocal";
import "./styles.css";

const DEMO_LOG = "[pcb-demo]";

function demoLog(message: string, detail?: Record<string, unknown> | null): void {
  if (detail != null) console.info(DEMO_LOG, message, detail);
  else console.info(DEMO_LOG, message);
}
function demoWarn(message: string, detail?: unknown): void {
  console.warn(DEMO_LOG, message, detail);
}
function demoError(message: string, detail?: unknown): void {
  console.error(DEMO_LOG, message, detail);
}

function summarizeDag(dag: KernelDag | null): Record<string, unknown> | null {
  if (!dag) return null;
  const dagObj = dag.DAG && typeof dag.DAG === "object" ? (dag.DAG as Record<string, unknown>) : {};
  const ser =
    dag.serializableNodes && typeof dag.serializableNodes === "object"
      ? (dag.serializableNodes as Record<string, unknown>)
      : {};
  return {
    version: dag.version,
    rootNodeId: dag.rootNodeId,
    dagNodeCount: Object.keys(dagObj).length,
    serializableTypeCount: Object.keys(ser).length,
  };
}

const FOUNDATION_IMPORT_PATH =
  (import.meta.env.VITE_FOUNDATION_IMPORT_PATH as string | undefined) ?? "cadbuildr.foundation";
const FOUNDATION_PACKAGE_NAME =
  (import.meta.env.VITE_FOUNDATION_PACKAGE_NAME as string | undefined) ?? "cadbuildr-foundation";
const FOUNDATION_VERSION =
  (import.meta.env.VITE_FOUNDATION_VERSION as string | undefined) ?? "^0.2.0";
const FOUNDATION_DAG_UTILS_PATH = `${FOUNDATION_IMPORT_PATH}.dag_utils`;

const PCB_IMPORT_PATH =
  (import.meta.env.VITE_PCB_IMPORT_PATH as string | undefined) ?? "cadbuildr.electronics";
const PCB_PACKAGE_REQUIREMENT =
  (import.meta.env.VITE_PCB_PACKAGE_REQUIREMENT as string | undefined) ?? "";

function resolvePcbWheelUrl(): string {
  const fromEnv = (import.meta.env.VITE_PCB_PACKAGE_WHEEL_URL as string | undefined)?.trim();
  if (fromEnv) return fromEnv;
  if (typeof window === "undefined") return "";
  return new URL(
    `${LOCAL_PCB_URL_SEGMENT}/${LOCAL_PCB_WHEEL_FILE}`,
    window.location.origin + import.meta.env.BASE_URL
  ).href;
}

/** Foundation / kernel STLs are Z-up; R3F is Y-up — lay the board flat. */
const MESH_SCENE_POSITION: [number, number, number] = [0, 0, 0];
const CAD_Z_UP_TO_Y_UP: [number, number, number] = [-Math.PI / 2, 0, 0];
const SCENE_BG = "#141a1c";

// Publishable keyId used when no `VITE_CADBUILDR_SDK_KEY_ID` is provided. This
// is the electronics project's public keyId (the `<keyId>` half of an
// `cbsdk_<keyId>_<secret>` partner key) — it is origin-locked to
// `https://cadbuildr.github.io` and carries no secret, so it is safe to ship in
// the static bundle. Override with the env var / repo secret for a different key.
const DEFAULT_SDK_KEY_ID = "a6d0604231520821";

type DemoMode = "components" | "boards";

type DemoEntry = {
  id: string;
  title: string;
  description: string;
  /** Camera distance hint — small parts want a tight framing. */
  camera: [number, number, number];
  buildPythonCode: () => string;
};

const SHOW_HEADER = `from ${FOUNDATION_IMPORT_PATH} import show`;

// --- Boards (full assemblies; components hidden by default via the tree) ---
const BOARDS: DemoEntry[] = [
  {
    id: "arduino-uno",
    title: "Arduino Uno",
    description:
      "The genuine Uno R3 edge-cut outline (chamfer + right-edge notch) populated with USB, ATmega DIP, crystal and the four header banks.",
    camera: [120, 110, 120],
    buildPythonCode: () =>
      `${SHOW_HEADER}\nfrom ${PCB_IMPORT_PATH}.boards import ArduinoUno\n\nshow(ArduinoUno())`,
  },
  {
    id: "arduino-nano",
    title: "Arduino Nano",
    description:
      "The compact 18 x 45 mm Nano: a TQFP ATmega328, two 1x15 header rows, mini-USB, crystal and indicator LEDs.",
    camera: [70, 70, 70],
    buildPythonCode: () =>
      `${SHOW_HEADER}\nfrom ${PCB_IMPORT_PATH}.boards import ArduinoNano\n\nshow(ArduinoNano())`,
  },
  {
    id: "raspberry-pi",
    title: "Raspberry Pi",
    description:
      "The 85 x 56 mm Pi Model B with rounded corners: 40-pin GPIO header, SoC QFP, stacked USB and an RJ45 Ethernet jack.",
    camera: [130, 120, 130],
    buildPythonCode: () =>
      `${SHOW_HEADER}\nfrom ${PCB_IMPORT_PATH}.boards import RaspberryPi\n\nshow(RaspberryPi())`,
  },
  {
    id: "raspberry-pi-pico",
    title: "Raspberry Pi Pico",
    description:
      "The 21 x 51 mm Pico: castellated 0.1\" headers down both edges, RP2040 in the centre, micro-USB and BOOTSEL button.",
    camera: [70, 70, 70],
    buildPythonCode: () =>
      `${SHOW_HEADER}\nfrom ${PCB_IMPORT_PATH}.boards import RaspberryPiPico\n\nshow(RaspberryPiPico())`,
  },
  {
    id: "esp32-devkit",
    title: "ESP32 DevKitC",
    description:
      "The ESP32 dev board: WROOM module up top, micro-USB + USB-serial bridge below, EN/BOOT buttons and two 1x19 headers.",
    camera: [90, 85, 90],
    buildPythonCode: () =>
      `${SHOW_HEADER}\nfrom ${PCB_IMPORT_PATH}.boards import ESP32DevKit\n\nshow(ESP32DevKit())`,
  },
];

// --- Individual components (single parts shown solo) ---
const COMPONENTS: DemoEntry[] = [
  {
    id: "resistor",
    title: "Resistor (axial)",
    description: "A through-hole axial resistor with colour-banded body and formed leads.",
    camera: [26, 22, 26],
    buildPythonCode: () =>
      `${SHOW_HEADER}\nfrom ${PCB_IMPORT_PATH} import Resistor\n\nshow(Resistor("220"))`,
  },
  {
    id: "led",
    title: "LED (5 mm)",
    description: "A 5 mm through-hole LED with domed lens and two leads.",
    camera: [22, 18, 22],
    buildPythonCode: () =>
      `${SHOW_HEADER}\nfrom ${PCB_IMPORT_PATH} import LED\n\nshow(LED("red"))`,
  },
  {
    id: "electrolytic-cap",
    title: "Electrolytic capacitor",
    description: "A radial electrolytic can with polarity stripe.",
    camera: [26, 22, 26],
    buildPythonCode: () =>
      `${SHOW_HEADER}\nfrom ${PCB_IMPORT_PATH} import ElectrolyticCapacitor\n\nshow(ElectrolyticCapacitor("47u"))`,
  },
  {
    id: "pin-header",
    title: "Pin header (2x10)",
    description: "A 2x10 0.1\" pin header — the workhorse board-to-board connector.",
    camera: [40, 32, 40],
    buildPythonCode: () =>
      `${SHOW_HEADER}\nfrom ${PCB_IMPORT_PATH} import PinHeader\n\nshow(PinHeader(positions=10, rows=2))`,
  },
  {
    id: "dip",
    title: "DIP-28 IC",
    description: "A 28-pin dual-in-line package with the classic notch and gull-wing leads.",
    camera: [55, 45, 55],
    buildPythonCode: () =>
      `${SHOW_HEADER}\nfrom ${PCB_IMPORT_PATH} import DIP\n\nshow(DIP(28))`,
  },
  {
    id: "qfp",
    title: "QFP-64 IC",
    description: "A quad-flat-pack with leads on all four sides — an SoC stand-in.",
    camera: [40, 34, 40],
    buildPythonCode: () =>
      `${SHOW_HEADER}\nfrom ${PCB_IMPORT_PATH} import QFP\n\nshow(QFP(64))`,
  },
  {
    id: "usb-a",
    title: "USB Type-A",
    description: "A full-size USB-A receptacle with metal shell.",
    camera: [40, 32, 40],
    buildPythonCode: () =>
      `${SHOW_HEADER}\nfrom ${PCB_IMPORT_PATH} import USBTypeA\n\nshow(USBTypeA())`,
  },
  {
    id: "rj45",
    title: "RJ45 jack",
    description: "An 8P8C Ethernet jack.",
    camera: [50, 40, 50],
    buildPythonCode: () =>
      `${SHOW_HEADER}\nfrom ${PCB_IMPORT_PATH} import RJ45\n\nshow(RJ45())`,
  },
  {
    id: "crystal",
    title: "Crystal (HC-49)",
    description: "A 16 MHz HC-49 crystal in a metal can.",
    camera: [26, 22, 26],
    buildPythonCode: () =>
      `${SHOW_HEADER}\nfrom ${PCB_IMPORT_PATH} import Crystal\n\nshow(Crystal("16MHz"))`,
  },
  {
    id: "tactile-button",
    title: "Tactile button",
    description: "A 6 mm tactile push-button switch.",
    camera: [26, 22, 26],
    buildPythonCode: () =>
      `${SHOW_HEADER}\nfrom ${PCB_IMPORT_PATH} import TactileButton\n\nshow(TactileButton())`,
  },
];

function buildFoundationCompatibilityScript(foundationImportPath: string): string {
  return `
from importlib import import_module
import sys
import types

foundation = import_module(${JSON.stringify(foundationImportPath)})
_submodules = ("gen", "gen.models", "gen.runtime", "dag_utils", "utils", "helpers", "constants")
for _prefix in ("cad_package", "cadbuildr"):
    legacy_alias = _prefix + ".foundation"
    sys.modules[legacy_alias] = foundation
    _root = sys.modules.get(_prefix)
    if _root is None:
        _root = types.ModuleType(_prefix)
        _root.__path__ = []
        sys.modules[_prefix] = _root
    setattr(_root, "foundation", foundation)
    for _suffix in _submodules:
        try:
            _mod = import_module(${JSON.stringify(foundationImportPath)} + "." + _suffix)
        except ModuleNotFoundError:
            continue
        sys.modules[legacy_alias + "." + _suffix] = _mod
`.trim();
}

/** Pyodide runtime patches `builtins.show`; rebind foundation exports so `from … import show` still captures the DAG. */
function buildFoundationShowRebindScript(foundationImportPath: string): string {
  return `
import builtins
from importlib import import_module

_root = import_module(${JSON.stringify(foundationImportPath)})
_dag_utils = import_module(${JSON.stringify(foundationImportPath)} + ".dag_utils")
_hook = builtins.show
_root.show = _hook
_dag_utils.show = _hook
`.trim();
}

function buildPcbInstallScript(args: {
  packageRequirement: string;
  wheelUrl?: string;
  importPath: string;
}): string {
  return `
import importlib
import micropip

wheel_url = ${JSON.stringify(args.wheelUrl ?? "")}
package_requirement = ${JSON.stringify(args.packageRequirement)}
import_path = ${JSON.stringify(args.importPath)}
install_errors = []

try:
    importlib.import_module(import_path)
    _needs_install = False
except Exception:
    _needs_install = True

if _needs_install and wheel_url:
    try:
        await micropip.install(wheel_url, deps=False)
    except Exception as error:
        install_errors.append(f"wheel install failed: {error}")

if _needs_install and package_requirement:
    try:
        await micropip.install(package_requirement, deps=False)
    except Exception as error:
        install_errors.append(f"package install failed: {error}")

try:
    importlib.import_module(import_path)
except Exception as error:
    message = "\\n".join(install_errors) if install_errors else "No install attempt was made."
    raise RuntimeError(
        "Failed to import PCB package '" + import_path + "'. "
        + message
        + "\\nLocal dev: run uv build in the Python package directory (parent of github-io/). "
        + "Production: copy the wheel to public/local-pcb/ or set VITE_PCB_PACKAGE_WHEEL_URL."
    ) from error
`.trim();
}

function App() {
  const [mode, setMode] = React.useState<DemoMode>("boards");
  const [activeBoardId, setActiveBoardId] = React.useState<string>(BOARDS[0].id);
  const [activeComponentId, setActiveComponentId] = React.useState<string>(COMPONENTS[0].id);
  const [dag, setDag] = React.useState<KernelDag | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [runtimeReady, setRuntimeReady] = React.useState(false);

  const pyodideRef = React.useRef<PyodideLike | null>(null);
  const runCounterRef = React.useRef(0);

  const isBoards = mode === "boards";

  const activeEntry = React.useMemo<DemoEntry>(() => {
    if (isBoards) {
      return BOARDS.find((b) => b.id === activeBoardId) ?? BOARDS[0];
    }
    return COMPONENTS.find((c) => c.id === activeComponentId) ?? COMPONENTS[0];
  }, [isBoards, activeBoardId, activeComponentId]);

  const pythonScript = React.useMemo(() => activeEntry.buildPythonCode(), [activeEntry]);

  const kernelApiBaseUrl = React.useMemo(() => resolveKernelApiBaseUrl(), []);
  // Auth: prefer a pre-minted sessionToken (local dev / SSR); otherwise use the
  // publishable keyId browser flow so the deployed GitHub Pages build mints a
  // short-lived cbv1 token from the hub (origin-locked) without baking a secret
  // into the static bundle.
  const sessionToken = React.useMemo(
    () => (import.meta.env.VITE_CADBUILDR_SESSION_TOKEN as string | undefined)?.trim() || undefined,
    []
  );
  const sdkKeyId = React.useMemo(
    () => (import.meta.env.VITE_CADBUILDR_SDK_KEY_ID as string | undefined)?.trim() || DEFAULT_SDK_KEY_ID,
    []
  );
  const hubBaseUrl = React.useMemo(
    () => (import.meta.env.VITE_CADBUILDR_HUB_BASE_URL as string | undefined)?.trim() || undefined,
    []
  );

  React.useEffect(() => {
    let cancelled = false;
    async function bootstrapRuntime() {
      try {
        setError(null);
        demoLog("bootstrap: starting (Pyodide + foundation + PCB wheel)");
        const pyodide = await initializeCadPyodideRuntime({
          packages: { foundation: FOUNDATION_VERSION, foundationPackageName: FOUNDATION_PACKAGE_NAME },
          foundationImportPath: FOUNDATION_IMPORT_PATH,
          foundationDagUtilsPath: FOUNDATION_DAG_UTILS_PATH,
        });
        if (cancelled) return;
        await pyodide.runPythonAsync(buildFoundationCompatibilityScript(FOUNDATION_IMPORT_PATH));
        await pyodide.runPythonAsync(buildFoundationShowRebindScript(FOUNDATION_IMPORT_PATH));
        await pyodide.runPythonAsync(
          buildPcbInstallScript({
            packageRequirement: PCB_PACKAGE_REQUIREMENT,
            wheelUrl: resolvePcbWheelUrl(),
            importPath: PCB_IMPORT_PATH,
          })
        );
        if (cancelled) return;
        pyodideRef.current = pyodide;
        setRuntimeReady(true);
        demoLog("bootstrap: ready", { pcbWheelUrl: resolvePcbWheelUrl(), kernelApiBaseUrl });
      } catch (runtimeError) {
        if (cancelled) return;
        const message = runtimeError instanceof Error ? runtimeError.message : String(runtimeError);
        demoError("bootstrap failed", runtimeError);
        setError(message);
      }
    }
    void bootstrapRuntime();
    return () => {
      cancelled = true;
    };
  }, []);

  React.useEffect(() => {
    if (!runtimeReady || !pyodideRef.current) return;
    const runId = ++runCounterRef.current;
    let cancelled = false;
    async function runExample() {
      try {
        setError(null);
        setDag(null);
        demoLog("runExample: executing Python", { runId, entry: activeEntry.id });
        const result = await runCadPythonCode(pyodideRef.current as PyodideLike, pythonScript, {
          foundationImportPath: FOUNDATION_IMPORT_PATH,
          foundationDagUtilsPath: FOUNDATION_DAG_UTILS_PATH,
        });
        if (cancelled || runId !== runCounterRef.current) return;
        const nextDag = (result.dag as KernelDag | null) ?? null;
        demoLog("runExample: DAG captured", summarizeDag(nextDag));
        if (!nextDag) demoWarn("runExample: DAG is null — kernel mesh will not render");
        setDag(nextDag);
      } catch (runError) {
        if (cancelled || runId !== runCounterRef.current) return;
        const message = runError instanceof Error ? runError.message : String(runError);
        demoError("runExample: Python failed", runError);
        setError(message);
      }
    }
    void runExample();
    return () => {
      cancelled = true;
    };
  }, [activeEntry.id, pythonScript, runtimeReady]);

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <header className="sidebar-header">
          <h1>CADbuildr PCB Demo</h1>
          <p>
            Parametric PCBs from Python — boards drill their own footprints and seat every
            part in one call. Toggle the tree to peel the components off the board.
          </p>
        </header>

        <div className="tab-bar" role="tablist" aria-label="Demo mode">
          <button
            type="button"
            role="tab"
            aria-selected={isBoards}
            className={`tab ${isBoards ? "active" : ""}`}
            onClick={() => setMode("boards")}
          >
            Boards
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={!isBoards}
            className={`tab ${!isBoards ? "active" : ""}`}
            onClick={() => setMode("components")}
          >
            Components
          </button>
        </div>

        {isBoards ? (
          <section className="example-list">
            {BOARDS.map((board) => (
              <button
                key={board.id}
                type="button"
                className={`example-button ${board.id === activeBoardId ? "active" : ""}`}
                onClick={() => setActiveBoardId(board.id)}
              >
                <span className="example-title">{board.title}</span>
                <span className="example-description">{board.description}</span>
              </button>
            ))}
          </section>
        ) : (
          <section className="component-picker">
            <label className="picker-label" htmlFor="component-select">
              Pick a component
            </label>
            <select
              id="component-select"
              className="component-select"
              value={activeComponentId}
              onChange={(event) => setActiveComponentId(event.target.value)}
            >
              {COMPONENTS.map((component) => (
                <option key={component.id} value={component.id}>
                  {component.title}
                </option>
              ))}
            </select>
            <p className="component-description">{activeEntry.description}</p>
          </section>
        )}

        <section className="code-card">
          <h2>Python</h2>
          <pre>{pythonScript}</pre>
        </section>
      </aside>

      <main className="canvas-panel">
        {error ? (
          <div className="canvas-overlay-error" role="alert">
            <pre>{error}</pre>
          </div>
        ) : null}
        <CadbuildrProvider
          baseUrl={kernelApiBaseUrl}
          hubBaseUrl={hubBaseUrl}
          projectKey="electronics"
          {...(sessionToken ? { sessionToken } : { keyId: sdkKeyId })}
        >
          <CadbuildrViewer
            dag={dag}
            background={SCENE_BG}
            cameraPosition={activeEntry.camera}
            fov={42}
            meshPosition={MESH_SCENE_POSITION}
            meshRotation={CAD_Z_UP_TO_Y_UP}
            showTree={isBoards}
            treeTitle={activeEntry.title}
            defaultHiddenNodeNames={isBoards ? ["components"] : undefined}
            loading={!runtimeReady}
            loadingLabel={!runtimeReady ? "Loading Python runtime…" : "Rendering…"}
            onRender={(meta) => {
              demoLog("CadbuildrViewer: render ready", meta);
              setError(null);
            }}
            onError={(meshError) => {
              demoError("CadbuildrViewer: render failed", meshError);
              setError(meshError.message);
            }}
          />
        </CadbuildrProvider>
      </main>
    </div>
  );
}

// Avoid StrictMode here: in dev it double-mounts effects and fires duplicate kernel-api renders.
ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(<App />);
