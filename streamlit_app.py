import streamlit as st
import numpy as np

st.set_page_config(page_title="THE ONE FOOTBALL", page_icon="🏈", layout="wide")

NFL_TEAMS = ["Arizona Cardinals", "Atlanta Falcons", "Baltimore Ravens", "Buffalo Bills",
    "Carolina Panthers", "Chicago Bears", "Cincinnati Bengals", "Cleveland Browns",
    "Dallas Cowboys", "Denver Broncos", "Detroit Lions", "Green Bay Packers",
    "Houston Texans", "Indianapolis Colts", "Jacksonville Jaguars", "Kansas City Chiefs",
    "Las Vegas Raiders", "Los Angeles Chargers", "Los Angeles Rams", "Miami Dolphins",
    "Minnesota Vikings", "New England Patriots", "New Orleans Saints", "New York Giants",
    "New York Jets", "Philadelphia Eagles", "Pittsburgh Steelers", "San Francisco 49ers",
    "Seattle Seahawks", "Tampa Bay Buccaneers", "Tennessee Titans", "Washington Commanders"]

POSITIONS = ["QB", "RB", "WR", "TE"]

POSITION_STATS = {
    "QB": ["passing_yards", "passing_tds", "rushing_yards"],
    "RB": ["rushing_yards", "rushing_tds", "receiving_yards"],
    "WR": ["receiving_yards", "receiving_tds", "receptions"],
    "TE": ["receiving_yards", "receiving_tds", "receptions"]
}

STATS = {
    "passing_yards": {"name": "Passing Yards", "base": 250},
    "passing_tds": {"name": "Passing TDs", "base": 1.5},
    "rushing_yards": {"name": "Rushing Yards", "base": 65},
    "rushing_tds": {"name": "Rushing TDs", "base": 0.5},
    "receiving_yards": {"name": "Receiving Yards", "base": 55},
    "receiving_tds": {"name": "Receiving TDs", "base": 0.4},
    "receptions": {"name": "Receptions", "base": 5.5}
}

DEF = {
    "Arizona Cardinals": {"pass": 28, "run": 22}, 
    "Dallas Cowboys": {"pass": 11, "run": 16},
    "Baltimore Ravens": {"pass": 8, "run": 5}, 
    "Kansas City Chiefs": {"pass": 13, "run": 12}
}

QUICK = {
    "QB": ["Dak Prescott", "Kyler Murray", "Patrick Mahomes"],
    "RB": ["Javonte Williams", "Bam Knight", "Saquon Barkley"],
    "WR": ["CeeDee Lamb", "Marvin Harrison Jr.", "George Pickens"],
    "TE": ["Jake Ferguson", "Trey McBride", "Travis Kelce"]
}

for k in ['games', 'players', 'conditions', 'current', 'results']:
    if k not in st.session_state:
        st.session_state[k] = [] if k in ['games', 'results'] else {} if k != 'current' else None

def calc_def(opp, stat):
    typ = "pass" if any(x in stat for x in ["passing", "receiving", "receptions"]) else "run"
    rank = DEF.get(opp, {}).get(typ, 16)
    if rank <= 5: return 0.80
    elif rank <= 10: return 0.88
    elif rank <= 16: return 0.95
    elif rank <= 24: return 1.0
    elif rank <= 28: return 1.12
    else: return 1.18

def project(player, pos, stat, opp, home, gid):
    base = STATS[stat]['base']
    
    adj = {
        ("QB", "rushing_yards"): 25, ("RB", "rushing_yards"): 75,
        ("RB", "receiving_yards"): 30, ("WR", "receiving_yards"): 65,
        ("WR", "receptions"): 6.0, ("TE", "receiving_yards"): 45,
        ("TE", "receptions"): 5.0
    }
    base = adj.get((pos, stat), base)
    
    df = calc_def(opp, stat)
    hf = 1.07 if home else 1.0
    
    cond = st.session_state.conditions.get(gid, {})
    tot = cond.get('total', 45)
    
    if tot >= 50: sf = 1.12
    elif tot >= 47: sf = 1.08
    elif tot >= 44: sf = 1.04
    else: sf = 1.0
    
    proj = base * df * hf * sf
    line = max(0, np.random.normal(proj, 5))
    tgt = line * 1.10
    
    conf = 65
    if df > 1.15: conf += 10
    elif df < 0.85: conf -= 10
    if home: conf += 3
    if sf > 1.08: conf += 5
    
    conf = np.clip(conf + np.random.uniform(-3, 3), 55, 85)
    
    return {
        'player': player, 'pos': pos, 'stat': STATS[stat]['name'],
        'line': round(line, 1), 'target': round(tgt, 1),
        'margin': round(tgt - line, 1), 'confidence': round(conf, 1),
        'opp': opp, 'home': home
    }

def odds(legs):
    o = {2: ("+264", 2.64), 3: ("+596", 5.96), 4: ("+1228", 11.28), 
         5: ("+2435", 23.35), 6: ("+4700", 47.0), 8: ("+9500", 95.0),
         10: ("+25000", 250.0), 12: ("+40000", 400.0)}
    return o.get(legs, ("+40000", 400.0))

st.title("🏈 THE ONE FOOTBALL")
st.caption("Built to Win 💰")

c1, c2, c3 = st.columns(3)
c1.metric("Games", len(st.session_state.games))
c2.metric("Props", len(st.session_state.results))
c3.metric("v9.0", "FINAL")

t1, t2, t3 = st.tabs(["Setup", "Players", "Results"])

with t1:
    st.subheader("Setup Game")
    c1, c2 = st.columns(2)
    
    with c1:
        away = st.selectbox("Away", [""] + NFL_TEAMS, key="a")
        home = st.selectbox("Home", [""] + NFL_TEAMS, key="h")
        
        if st.button("Create", type="primary"):
            if away and home and away != home:
                g = f"{away} @ {home}"
                if g not in st.session_state.games:
                    st.session_state.games.append(g)
                    st.session_state.players[g] = []
                    st.success("✅")
                    st.rerun()
    
    with c2:
        if st.session_state.games:
            sel = st.selectbox("Select", st.session_state.games)
            tot = st.number_input("O/U", 30.0, 65.0, 48.5, 0.5)
            
            if st.button("Activate", type="primary"):
                st.session_state.conditions[sel] = {'total': tot}
                st.session_state.current = sel
                st.success("✅")
                st.rerun()

with t2:
    st.subheader("Add Players")
    
    if not st.session_state.current:
        st.warning("Setup game first")
    else:
        teams = st.session_state.current.split(" @ ")
        
        c1, c2 = st.columns(2)
        with c1:
            tm = st.selectbox("Team", teams)
            meth = st.radio("Method", ["Quick", "Manual"], horizontal=True)
            
            if meth == "Quick":
                p = st.selectbox("Pos", POSITIONS, key="qp")
                n = st.selectbox("Player", QUICK[p], key="qn")
            else:
                p = st.selectbox("Pos", POSITIONS, key="mp")
                n = st.text_input("Name", key="mn")
            
            if st.button("ADD", type="primary"):
                if n:
                    if st.session_state.current not in st.session_state.players:
                        st.session_state.players[st.session_state.current] = []
                    
                    ex = [x['name'] for x in st.session_state.players[st.session_state.current]]
                    if n not in ex:
                        st.session_state.players[st.session_state.current].append(
                            {'name': n, 'pos': p, 'team': tm}
                        )
                        
                        hm = (tm == teams[1])
                        op = teams[1] if tm == teams[0] else teams[0]
                        
                        for s in POSITION_STATS[p]:
                            res = project(n, p, s, op, hm, st.session_state.current)
                            st.session_state.results.append(res)
                        
                        st.success(f"✅ {n}")
                        st.rerun()
        
        with c2:
            st.markdown("**Players**")
            if st.session_state.current in st.session_state.players:
                for i, pl in enumerate(st.session_state.players[st.session_state.current]):
                    ca, cb = st.columns([4, 1])
                    ca.write(f"{pl['name']} ({pl['pos']})")
                    if cb.button("🗑️", key=f"d{i}"):
                        rm = st.session_state.players[st.session_state.current][i]['name']
                        st.session_state.players[st.session_state.current].pop(i)
                        st.session_state.results = [r for r in st.session_state.results if r['player'] != rm]
                        st.rerun()

with t3:
    st.subheader("Results")
    
    if not st.session_state.results:
        st.info("Add players")
    else:
        thr = st.slider("Min Conf %", 50, 85, 60, 5)
        filt = [r for r in st.session_state.results if r['confidence'] >= thr]
        
        st.markdown(f"**{len(filt)} props ≥ {thr}%**")
        
        if filt:
            for r in filt:
                em = "🟢" if r['confidence'] >= 70 else "🟡"
                with st.expander(f"{em} {r['player']} - {r['stat']} | {r['confidence']}%"):
                    ca, cb, cc = st.columns(3)
                    ca.metric("Line", r['line'])
                    cb.metric("Target", r['target'])
                    cc.metric("Conf", f"{r['confidence']}%")
            
            if len(filt) >= 2:
                st.markdown("---")
                st.markdown("**Parlay Builder**")
                
                legs = st.slider("Legs", 2, min(12, len(filt)), 6)
                parl = filt[:legs]
                prob = np.prod([x['confidence']/100 for x in parl]) * 100
                od_str, mult = odds(legs)
                
                ca, cb, cc = st.columns(3)
                ca.metric("Prob", f"{prob:.2f}%")
                cb.metric("Odds", od_str)
                cc.metric("EV", f"{((prob/100*mult-1)*100):+.0f}%")
                
                st.markdown("**Your Parlay:**")
                for i, x in enumerate(parl, 1):
                    st.write(f"{i}. {x['player']} OVER {x['line']} {x['stat']}")
                
                bet = st.number_input("Bet $", 10, 1000, 100, 10)
                st.success(f"Win: ${bet * mult:,.0f}")
                
                st.markdown("**Copy:**")
                output = ""
                for i, x in enumerate(parl, 1):
                    output += f"{i}. {x['player']} OVER {x['line']} {x['stat']}
"
                st.code(output)

st.markdown("---")
st.caption("🏈 THE ONE FOOTBALL v9.0")