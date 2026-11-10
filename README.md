<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="./assets/card-dark.svg">
    <source media="(prefers-color-scheme: light)" srcset="./assets/card-light.svg">
    <img src="./assets/card-dark.svg" alt="noah@leibovitz profile card: a rotating ASCII-art portrait beside a summary. Computer Science and Business at the University of Maryland (May 2029), President's Scholar, software engineering intern at Gulf Coast Estate Care." width="940">
  </picture>
</p>

<p align="center">
  <a href="https://www.linkedin.com/in/noah-leibovitz"><img src="https://img.shields.io/badge/LinkedIn-0A66C2?style=for-the-badge" alt="LinkedIn"></a>
  <a href="mailto:noah.leibovitz@outlook.com"><img src="https://img.shields.io/badge/Email-C8102E?style=for-the-badge" alt="Email"></a>
</p>

---

### ✦ Featured work

<table>
<tr>
<td width="50%" valign="top">

#### [Argus](https://github.com/NLBoa/Argus)
Always-on course hub that runs on a Raspberry Pi 4B. It pulls deadlines, announcements and course materials from Canvas, Gradescope, Piazza and umd.io, estimates the effort, ranks the work into a queue for my work windows, and reminds me by text. Deadline alerts are **deterministic and never depend on AI**. A **read-only MCP server** lets Claude read the collected deadlines to plan my week, and the dashboard is reachable from anywhere over Tailscale.

`Python` `SQLite` `Raspberry Pi` `MCP` `Tailscale`

</td>
<td width="50%" valign="top">

#### [Smart Display](https://github.com/Sheel2007/OMEGA-WB)
Touchscreen home board for our apartment, running full screen on a Raspberry Pi and built with two roommates. I built the **Zigbee lighting** (pairing, schedules, motion-sensor control, low-battery alerts; setup in [zigbee_ceiling](https://github.com/NLBoa/zigbee_ceiling)), the Spotify widget, the Sports page with live scores, line-ups and a game-day countdown, the barcode-scan grocery list, and the layout that lets you move and resize widgets. A standard-library Python server and plain HTML/CSS/JS, with no build step.

`Python` `JavaScript` `Raspberry Pi` `Zigbee/MQTT` `Spotify API`

</td>
</tr>
<tr>
<td width="50%" valign="top">

#### [Jupiterp](https://github.com/atcupps/Jupiterp/pull/975)
Open-source course scheduler for University of Maryland students, live at [jupiterp.com](https://jupiterp.com). My merged contribution **syncs the Course Planner into the Schedule Generator**: the courses a student has planned fill in the generator automatically and stay in step as the plan changes, so nobody re-enters them. Shipped with 200+ lines of new tests.

`Svelte` `TypeScript` `Open source`

</td>
<td width="50%" valign="top">

#### [Aegis Orbit](https://github.com/KingXaney/Aegis-Orbit-)
Hackathon team project: a satellite collision-avoidance simulator. An XGBoost ranker scans an **18,598-object orbital catalog**, physics screening confirms the threats, and an agent plans and explains avoidance burns on a 3D CesiumJS globe. I built the catalog-explorer home page (live globe, search and filters, loading states), the sandbox flight-deck HUD, and the "ghost" replays that show the collision a burn avoided. ([live demo](https://aegis-orbit-liart.vercel.app))

`React` `TypeScript` `CesiumJS` `FastAPI` `XGBoost`

</td>
</tr>
</table>

### ✦ Toolbox

| | |
|---|---|
| **Languages** | ![C#](https://img.shields.io/badge/C%23-239120?style=flat-square) ![Java](https://img.shields.io/badge/Java-ED8B00?style=flat-square&logo=openjdk&logoColor=white) ![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white) ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=flat-square&logo=postgresql&logoColor=white) ![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=flat-square&logo=javascript&logoColor=black) ![HTML/CSS](https://img.shields.io/badge/HTML%2FCSS-E34F26?style=flat-square&logo=html5&logoColor=white) |
| **Web & Backend** | ![React](https://img.shields.io/badge/React-20232A?style=flat-square&logo=react&logoColor=61DAFB) ![Node.js](https://img.shields.io/badge/Node.js-5FA04E?style=flat-square&logo=nodedotjs&logoColor=white) ![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white) ![.NET / Razor Pages](https://img.shields.io/badge/.NET%20%2F%20Razor%20Pages-512BD4?style=flat-square&logo=dotnet&logoColor=white) |
| **Cloud & Tools** | ![Git](https://img.shields.io/badge/Git-F05032?style=flat-square&logo=git&logoColor=white) ![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white) ![Google Cloud](https://img.shields.io/badge/Google%20Cloud-4285F4?style=flat-square&logo=googlecloud&logoColor=white) ![Azure](https://img.shields.io/badge/Azure-0078D4?style=flat-square) ![VS Code](https://img.shields.io/badge/VS%20Code-007ACC?style=flat-square) ![Visual Studio](https://img.shields.io/badge/Visual%20Studio-5C2D91?style=flat-square) ![IntelliJ IDEA](https://img.shields.io/badge/IntelliJ%20IDEA-000000?style=flat-square&logo=intellijidea&logoColor=white) ![Eclipse](https://img.shields.io/badge/Eclipse-2C2255?style=flat-square&logo=eclipseide&logoColor=white) |
| **Libraries** | ![pandas](https://img.shields.io/badge/pandas-150458?style=flat-square&logo=pandas&logoColor=white) ![NumPy](https://img.shields.io/badge/NumPy-013243?style=flat-square&logo=numpy&logoColor=white) ![Matplotlib](https://img.shields.io/badge/Matplotlib-11557C?style=flat-square) ![JUnit](https://img.shields.io/badge/JUnit-25A162?style=flat-square&logo=junit5&logoColor=white) |
| **Hardware** | ![Raspberry Pi](https://img.shields.io/badge/Raspberry%20Pi-A22846?style=flat-square&logo=raspberrypi&logoColor=white) ![Zigbee](https://img.shields.io/badge/Zigbee-EB0443?style=flat-square&logo=zigbee&logoColor=white) ![MQTT](https://img.shields.io/badge/MQTT-660066?style=flat-square&logo=mqtt&logoColor=white) |

### ✦ More projects

| | |
|---|---|
| **[Java Shell](https://github.com/NLBoa/Java-Shell)** | POSIX-style shell written from scratch in Java: bash-style quoting, pipelines, output redirection and background jobs |
| **[Scheduling engine](https://github.com/NLBoa/GulfCoastEstatesSchedulingDemo)** | Demo of the C# scheduling engine from my Gulf Coast Estate Care internship: per-employee capacity across 3 license tiers, with recurring contracts booked all-or-nothing |
| **SKIBUS** | Check-in and boarding system in C#, Razor Pages and SQL that cut student check-in time roughly 10x across 180+ person-trips; led a 5-person student team over 4 seasons |
| **[UMD event feed](https://github.com/NLBoa/BitcampCloudforceProj)** | Bitcamp hackathon team project: scrapers for the UMD calendar, TerpLink and Reddit feeding a FastAPI events API with filtering and tagging |
| **[LED matrix grad cap](https://github.com/NLBoa/RGBMATRIXIMAGE)** | Graduation cap with an RGB LED matrix driven by a Raspberry Pi |

<!--
How this page is made
  profile.toml          the text on the right half of the card
  tools/ascii_face.py   turns a head-turn video into the ASCII frames
  tools/build_card.py   builds assets/card-dark.svg and assets/card-light.svg
-->
