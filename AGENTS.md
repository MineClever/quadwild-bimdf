# Repository Guidelines

## Project Structure & Module Organization
`quadwild/` contains the main CLI entry points, including `quadwild` and `cli_trace`. `components/quad_from_patches/` builds the second main executable, while `components/viz_mesh_results/` contains visualization tooling. Core Bi-MDF and quad retopology logic lives in `libs/quadretopology/quadretopology/`, especially `qr_flow.cpp`. Runtime configs are JSON files under `quadwild/`, `config/prep_config/`, `config/main_config/`, and `config/satsuma/`. Build logic starts at the root [CMakeLists.txt](/D:/_Code_Here/Git/quadwild-bimdf/CMakeLists.txt).

## Build, Test, and Development Commands
Configure and build locally with:

```sh
cmake . -B build -DSATSUMA_ENABLE_BLOSSOM5=0
cmake --build build
```

Run the main pipeline with:

```sh
./build/Build/bin/quadwild path/to/mesh.obj 2 config/prep_config/basic_setup.json
./build/Build/bin/quad_from_patches path/to/mesh_rem_p0.obj 123 config/main_config/flow_noalign_lemon.json
```

For a release-style Linux or macOS build, follow the CI pattern and add `-GNinja -DCMAKE_BUILD_TYPE=Release`. On Windows, CI uses `cmake . -B build -T "ClangCl"`.

## Coding Style & Naming Conventions
Use modern C++ as configured by CMake: C++20, no compiler extensions. Follow the existing style in `quadwild.cpp`: 4-space indentation, opening braces on a new line for functions and control blocks, `camelCase` for local variables, and descriptive snake_case filenames such as `qr_flow.cpp`. Keep includes grouped with standard headers first, then project headers. No formatter or linter is configured in-tree, so match surrounding code exactly.

## Testing Guidelines
There is no top-level first-party test target wired into the root build. Validate changes by rebuilding the affected targets and running the relevant CLI workflow with sample meshes and config files. If you add tests, prefer CTest-compatible CMake targets near the code they cover and name them after the feature or executable they exercise.

## Commit & Pull Request Guidelines
Recent history uses short, imperative subjects such as `Fix: Add missing return values...`, `CMake: FetchContent settings`, and `update xfield_tracer`. Keep commit titles concise and scope-first when useful. PRs should state what changed, why it changed, which commands were run to verify it, and include sample output or screenshots for visualization changes.

## Configuration Tips
Use `git clone --recursive` because this repository depends on bundled submodules in `libs/`. Prefer `QUADRETOPOLOGY_WITH_GUROBI=OFF` unless you are explicitly working on the optional Gurobi path.

## Agent Workflow Constraints
All repository work must be tracked in `temp/plan/` using the milestone planning system. Before starting any non-trivial task, create or update `temp/plan/<task>_plan.md` and `temp/plan/<task>_done_plan.md`, then sync summary status back to `temp/plan/plan.md`. Plan documents should default to Chinese for headings, status notes, and milestone details unless a task specifically requires English. Use explicit milestone phases such as `M1 - Design`, `M2 - Implementation`, `M3 - Validation`, and `M4 - Closeout`; do not execute work without an active tracked plan entry.

Treat bundled submodules under `libs/` as read-only by default. Do not modify files inside a submodule worktree unless the user explicitly asks for a submodule change. If a fix appears to require editing a submodule, stop, surface that constraint, and get explicit approval before changing it. Exception: `libs/xfield_tracer` is now intentionally maintained as local in-tree code rather than a protected submodule, so direct edits there are allowed when relevant to the task.

If new third-party functionality is needed, prefer reusing a mature upstream library over building a custom replacement. The user explicitly allows fetching such dependencies from GitHub as git submodules when appropriate, but only after confirming the dependency is genuinely needed and fits the repository structure better than an in-tree custom implementation.
