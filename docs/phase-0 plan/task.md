# Tasks: EBCA Rebuild (Step 0 Execution)

- `[x]` Step 0: Implement base simulation and physical runner (`D:\ebca\carl_simulation.py`)
  - `[x]` Set up abstract `HardwareInterface` and concrete `SimulationHAL` (MuJoCo wrapper)
  - `[x]` Implement continuous-to-spiking Poisson rate encoder and LIF SNN reflex motor neurons
  - `[x]` Set up main control loop at 30 Hz (physics loop at 240 Hz)
  - `[x]` Implement throttled RLS update scheduler (5 Hz baseline, 10 Hz surprise override, 100 ms cooldown)
  - `[x]` Implement event-driven HDC update checks
  - `[x]` Integrate crash safeguards (Auto-Teleport boundary watcher and NaN/Inf clamping)
  - `[x]` Add real-time performance profiler prints (cProfile / time counters)
  - `[x]` Inject simple sinusoidal joint/motor commands to verify actuator interfaces
- `[x]` Verification & Validation
  - `[x]` Run simulation script and verify MuJoCo viewer loads model successfully
  - `[x]` Verify telemetry logs show correct Diagnostic IDs and execution times
  - `[x]` Confirm wheels rotate and neck pivots under sinusoidal test signals
