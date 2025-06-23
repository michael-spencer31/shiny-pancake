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
    const option1 = new Option(team, team);
    const option2 = new Option(team, team);
    team1Select.appendChild(option1);
    team2Select.appendChild(option2);
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
      : `${data.winner} defeated ${data.team1 === data.winner ? data.team2 : data.team1} ${data.team1 === data.winner ? data.score1 : data.score2}-${data.team1 === data.winner ? data.score2 : data.score1}`;

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
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ team1, team2 })
    });

    const data = await res.json();

    if (res.status !== 200) {
      resultDiv.textContent = data.error || "Error simulating selected game.";
    } else {
      const text = data.tie
        ? `${data.team1} and ${data.team2} tied ${data.score1}-${data.score2}`
        : `${data.winner} defeated ${data.team1 === data.winner ? data.team2 : data.team1} ${data.team1 === data.winner ? data.score1 : data.score2}-${data.team1 === data.winner ? data.score2 : data.score1}`;
      resultDiv.textContent = text;
    }

    resultDiv.style.display = "block";
  } catch (error) {
    alert("Failed to simulate selected game.");
    console.error(error);
  }
}

function simulateGameWithScorers() {
  const team1 = document.getElementById("team1").value;
  const team2 = document.getElementById("team2").value;
  const resultDiv = document.getElementById("gameWithScorersResult");

  resultDiv.innerHTML = "";
  resultDiv.style.display = "none";

  fetch("/api/simulate-specific-game-with-goals", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ team1, team2 })
  })
    .then(res => {
      if (!res.ok) {
        return res.text().then(text => {
          throw new Error(`Server error: ${res.status} - ${text}`);
        });
      }
      return res.json();
    })
    .then(data => {

      const formatGoal = goal => {
        const assistText = goal.assists.length
          ? ` (Assists: ${goal.assists.join(', ')})`
          : "";
        return `<div>${goal.scorer}${assistText}</div>`;
      };

      const team1Goals = data.goals_team1.map(formatGoal).join("");
      const team2Goals = data.goals_team2.map(formatGoal).join("");

      resultDiv.innerHTML = `
        <h3>${data.team1} ${data.score1} - ${data.score2} ${data.team2}</h3>
        <p><strong>${data.tie ? `Tie (OT Winner: ${data.winner})` : `Winner: ${data.winner}`}</strong></p>
        <div style="margin-bottom: 10px;">
          <h4>${data.team1} Goals:</h4>
          ${team1Goals || "<div>None</div>"}
        </div>
        <div>
          <h4>${data.team2} Goals:</h4>
          ${team2Goals || "<div>None</div>"}
        </div>
      `;
      resultDiv.style.display = "block";
    })
    .catch(err => {
      console.error("❌ Error in simulateGameWithScorers:", err);
      resultDiv.innerHTML = `<p style="color: red;">Error: ${err.message}</p>`;
      resultDiv.style.display = "block";
    });
}


window.onload = fetchTeamStrengths;
