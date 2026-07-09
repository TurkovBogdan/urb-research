---
name: responsive-testing-process
description: "How to browser-test responsive work on KDE/X11 — open a controlled MCP tab, ask the user to pop it into its own window, then resize that window with xdotool + screenshot with import"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 144279a2-bbde-4ada-ac7b-4165cbb590d9
---

Standard process for testing interface adaptation (responsive) work in the browser.

**Box is KDE Plasma on X11 (`kwin_x11`), NOT a tiling WM** (earlier note was wrong). `DISPLAY=:0` is reachable from the shell.

**The agent CAN drive viewport widths itself on this box (2026-06-08) — this is the canonical workflow.** What does NOT work: the MCP `resize_window` tool and DevTools shortcuts (Ctrl+Shift+M / F12) — MCP keystrokes go to page content, never to Chrome's own UI, and `resize_window` leaves `window.innerWidth` unchanged. The procedure (confirmed end-to-end):

1. **Open the page in an MCP tab** (`tabs_create_mcp` → `navigate`), so it's under agent control.
2. **Ask the user to pop that tab into its own window** (drag the tab out). REQUIRED — a tab sharing a window with others can't be sized independently. Wait for the user to confirm it's separated.
3. **Find + confirm the window:** `xdotool search --class google-chrome` lists candidates; resize one (`xdotool windowsize <id> 1100 850`) and read `window.innerWidth` via the MCP `javascript_tool` — the candidate whose innerWidth changes is the MCP tab's window. (Needs `wmctrl`+`xdotool`: `sudo apt install -y wmctrl xdotool`; if maximized, first `wmctrl -i -r <id> -b remove,maximized_vert,maximized_horz`.)
4. **Crank the size per breakpoint** with `xdotool windowsize <id> <w> <h>`. **Chrome clamps min width ≈532px** — fine, still below the `md`/959 mobile cutoff.
5. **Screenshot the window from the shell** with `import -window <id> /tmp/x.png` (ImageMagick) and Read it. The MCP `computer` screenshot captures at a scaled/device resolution and can mislead on HiDPI — prefer `import` + reading `innerWidth` for ground truth.

Vite HMR makes fixes appear live — re-screenshot after each edit. Mobile chrome cutoff is `md` (<960px) (`mobileBreakpoint: 'md'`). The DS breakpoints page `/design-system/breakpoints` (live `useDisplay()` indicator) is still handy as a width readout. Fallback if shell-resize ever fails: open tabs on the breakpoints page and have the USER set widths.
