let teamList = [];

async function fetchTeamStrengths() {
  try {
    const res = await fetch("http://localhost:5000/api/team-strengths");
    const data = await res.json();
    teamList = Object.keys(data);
    populateTeamSelectors();
  } catch (error) {
    console.error("Failed to load team list:", error);
  }
}

function populateTeamSelectors() {
  const team1Select = document.getElementById("team1");
  const team2Select = document.getElementById("team2");

  team1Select.innerHTML = "";
  team2Select.innerHTML = "";

  teamList.forEach(team => {
    team1Select.appendChild(new Option(team, team));
    team2Select.appendChild(new Option(team, team));
  });

  if (teamList.length > 1) {
    team2Select.selectedIndex = 1;
  }
}

async function simulateSeason() {
  const table = document.getElementById("standingsTable");
  const tbody = table.querySelector("tbody");

  tbody.innerHTML = "";
  table.style.display = "none";

  try {
    const res = await fetch("http://localhost:5000/api/simulate-season");
    const data = await res.json();

    data.standings.forEach(team => {
      const row = document.createElement("tr");
      row.innerHTML = `
        <td>${team.rank}</td>
        <td>${team.team}</td>
        <td>${team.points}</td>
        <td>${team.wins}</td>
        <td>${team.games_played}</td>
        <td>${team.goal_diff}</td>
        <td>${team.biggest_win.score} vs ${team.biggest_win.opponent}</td>
      `;
      tbody.appendChild(row);
    });

    table.style.display = "table";
  } catch (error) {
    alert("Failed to simulate season. Make sure the Flask server is running.");
    console.error(error);
  }
}

async function simulateGame() {
  const resultDiv = document.getElementById("gameResult");

  resultDiv.style.display = "none";
  resultDiv.textContent = "";

  try {
    const res = await fetch("http://localhost:5000/api/simulate-game");
    const data = await res.json();

    const text = data.tie
      ? `${data.team1} and ${data.team2} tied ${data.score1}-${data.score2}`
      : `${data.winner} defeated ${
          data.team1 === data.winner ? data.team2 : data.team1
        } ${
          data.team1 === data.winner ? data.score1 : data.score2
        }-${data.team1 === data.winner ? data.score2 : data.score1}`;

    resultDiv.textContent = text;
    resultDiv.style.display = "block";
  } catch (error) {
    alert("Failed to simulate random game.");
    console.error(error);
  }
}

async function simulateSpecificGame() {
  const team1 = document.getElementById("team1").value;
  const team2 = document.getElementById("team2").value;
  const resultDiv = document.getElementById("specificGameResult");

  resultDiv.style.display = "none";
  resultDiv.textContent = "";

  if (team1 === team2) {
    resultDiv.textContent = "Please select two different teams.";
    resultDiv.style.display = "block";
    return;
  }

  try {
    const res = await fetch("http://localhost:5000/api/simulate-specific-game", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ team1, team2 })
    });

    const data = await res.json();

    if (res.status !== 200) {
      resultDiv.textContent = data.error || "Error simulating selected game.";
    } else {
      const text = data.tie
        ? `${data.team1} and ${data.team2} tied ${data.score1}-${data.score2}`
        : `${data.winner} defeated ${
            data.team1 === data.winner ? data.team2 : data.team1
          } ${
            data.team1 === data.winner ? data.score1 : data.score2
          }-${data.team1 === data.winner ? data.score2 : data.score1}`;
      resultDiv.textContent = text;
    }

    resultDiv.style.display = "block";
  } catch (error) {
    alert("Failed to simulate selected game.");
    console.error(error);
  }
}

async function simulateGameWithScorers() {
  const team1 = document.getElementById("team1").value;
  const team2 = document.getElementById("team2").value;
  const resultDiv = document.getElementById("gameWithScorersResult");

  resultDiv.innerHTML = "";
  resultDiv.style.display = "none";

  try {
    const res = await fetch("/api/simulate-specific-game-with-goals", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ team1, team2 })
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(`Server error: ${res.status} - ${text}`);
    }

    const data = await res.json();
    console.log("✅ Received game data:", data);

    const allGoals = [...data.goals_team1, ...data.goals_team2].map(g => ({
      ...g,
      teamName: g.team === 1 ? data.team1 : data.team2,
      prefix: g.team === 1 ? `${data.team1} Goal` : `${data.team2} Goal`
    }));

    const goalsByPeriod = {};
    for (const goal of allGoals) {
      if (!goalsByPeriod[goal.period]) {
        goalsByPeriod[goal.period] = [];
      }
      goalsByPeriod[goal.period].push(goal);
    }

    const sortedPeriods = Object.keys(goalsByPeriod).sort((a, b) => a - b);
    sortedPeriods.forEach(p => {
      goalsByPeriod[p].sort((a, b) => a.time.localeCompare(b.time));
    });

    // Final scores
    let finalScore1 = data.score1;
    let finalScore2 = data.score2;

    if (data.tie && data.winner === data.team1) {
      finalScore1 += 1;
    } else if (data.tie && data.winner === data.team2) {
      finalScore2 += 1;
    }

    let scoreLine = `${finalScore1} - ${finalScore2}`;
    if (data.tie) {
      scoreLine += " OT";
    }

    // Team logos
    const logo1 = `<img src="static/images/${data.team1}.png" alt="${data.team1} logo" style="height: 24px; vertical-align: middle;" onerror="this.onerror=null; this.src='static/images/default.png';">`;
    const logo2 = `<img src="static/images/${data.team2}.png" alt="${data.team2} logo" style="height: 24px; vertical-align: middle;" onerror="this.onerror=null; this.src='static/images/default.png';">`;


    // Start building output
    let output = `
      <h3>${logo1} ${data.team1} ${scoreLine} ${data.team2} ${logo2}</h3>
      <p><strong>${
        data.tie ? `OT Winner: ${data.winner}` : `Winner: ${data.winner}`
      }</strong></p>
    `;

    // Add goal summaries
    for (const period of sortedPeriods) {
      const periodLabel = period === "4" ? "OT" : `Period ${period}`;
      output += `<h4>${periodLabel}</h4>`;

      for (const goal of goalsByPeriod[period]) {
        const assists = goal.assists.length
          ? ` (Assists: ${goal.assists.join(", ")})`
          : "";

        const teamLogo = `<img src="static/images/${goal.teamName}.png" alt="${goal.teamName} logo" style="height: 20px; vertical-align: middle; margin-right: 6px;" onerror="this.onerror=null; this.src='static/images/default.png';">`;

        output += `<p>${teamLogo}${goal.prefix}: ${goal.time} – ${goal.scorer}${assists}</p>`;
      }
    }



    resultDiv.innerHTML = output;
    resultDiv.style.display = "block";

  } catch (err) {
    console.error("❌ Error in simulateGameWithScorers:", err);
    resultDiv.innerHTML = `<p style="color: red;">Error: ${err.message}</p>`;
    resultDiv.style.display = "block";
  }
}

window.onload = fetchTeamStrengths;
