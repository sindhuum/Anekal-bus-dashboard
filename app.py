import hmac

import pandas as pd
import plotly.express as px
import streamlit as st

from dashboard import BANDS, DISTANCE_BANDS, LEVELS, ROUTES, ZONES, build

st.set_page_config(page_title="Anekal Public Transportation Dashboard", page_icon="🚌", layout="wide")

BLUE, RED = "#1f4e78", "#d1383a"
LEVEL_COLORS = dict(zip(LEVELS, ["#2e9d5b", "#e6a817", "#e8772e", RED]))
MENUS = [("zone", "🗺️ Area", ZONES), ("band", "🕐 Time of day", BANDS), ("route", "🚌 Route", ROUTES)]
DEFAULTS = {"zone": "a", "band": "a", "route": "a"}


# ---------- Login ----------
def credentials():
    try:
        return st.secrets["USERNAME"], st.secrets["PASSWORD"]
    except Exception:
        return "anekal", "Bus@2026"  # demo default; set real values in Streamlit secrets


def login_page():
    st.title("🚌 Anekal Public Transportation Dashboard")
    _, mid, _ = st.columns([1, 1.2, 1])
    with mid:
        with st.form("login"):
            st.subheader("Sign in")
            st.caption("Enter your username and password to view the dashboard.")
            user = st.text_input("Username")
            pw = st.text_input("Password", type="password")
            if st.form_submit_button("Log in", use_container_width=True):
                u, p = credentials()
                if hmac.compare_digest(user, u) and hmac.compare_digest(pw, p):
                    st.session_state.auth = True
                    st.rerun()
                st.error("Incorrect username or password.")


if not st.session_state.get("auth"):
    login_page()
    st.stop()

# ---------- State ----------
for k, v in DEFAULTS.items():
    st.session_state.setdefault(k, v)
st.session_state.setdefault("view", "home")


def show_dashboard():
    st.session_state.view = "dash"


def reset():
    st.session_state.update(DEFAULTS)
    st.session_state.view = "dash"


def label(opts, v):
    return dict(opts)[v]


# ---------- Sidebar menus ----------
with st.sidebar:
    st.header("Choose what to see")
    for key, title, opts in MENUS:
        with st.expander(f"{title}: {label(opts, st.session_state[key])}"):
            st.radio(title, [o[0] for o in opts], key=key, format_func=lambda v, o=opts: label(o, v),
                     on_change=show_dashboard, label_visibility="collapsed")
    st.button("↺ Reset filters", on_click=reset, use_container_width=True)
    st.button("🏠 Home", on_click=lambda: st.session_state.update(view="home"), use_container_width=True)
    if st.button("Log out", use_container_width=True):
        st.session_state.clear()
        st.rerun()

data = build(st.session_state.zone, st.session_state.band, st.session_state.route)
st.title("🚌 Anekal Public Transportation Dashboard")


def bars(rows, color=BLUE, height=None):
    df = pd.DataFrame(rows, columns=["name", "value"])
    fig = px.bar(df, x="value", y="name", orientation="h", text="value", color_discrete_sequence=[color])
    fig.update_layout(yaxis={"autorange": "reversed", "title": ""}, xaxis_title="", height=height or max(200, 36 * len(df)),
                      margin=dict(l=0, r=10, t=10, b=10))
    return fig


# ---------- Home ----------
if st.session_state.view == "home":
    st.info("This dashboard shows how well city buses (BMTC) serve Anekal: where buses go, when they run, and which areas get very few.")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("How to use it")
        st.markdown("1. Open a menu on the left: **Area**, **Time of day** or **Route**.\n"
                    "2. Choose an option, for example “Evening rush”.\n"
                    "3. The charts change. Scroll down to read what it means.")
    with c2:
        st.subheader("Quick facts about Anekal town")
        st.markdown("- About 59 bus stops and 55 routes serve the town.\n- Around 894 bus trips run in a day.\n"
                    "- The busiest time is around 10 in the morning.\n- No direct bus goes to Electronic City or Hosur.\n"
                    "- 23 of the 59 stops get fewer than 10 buses a day.")
    st.subheader("Which routes run most often?")
    st.caption("A longer bar means more bus trips a day.")
    st.plotly_chart(bars(data["top_routes"]))
    st.stop()

# ---------- Dashboard ----------
st.caption("  ·  ".join(f"{t}: {label(o, st.session_state[k])}" for k, t, o in MENUS))
m1, m2, m3 = st.columns(3)
m1.metric("Bus stops", data["stops"])
m2.metric("Bus routes", data["routes"])
m3.metric("Bus trips in a day", f"{data['trips']:,}")

a, b = st.columns(2)
with a:
    st.subheader("When do buses run?")
    st.caption("Each bar is one hour of the day. A taller bar means more buses.")
    hd = pd.DataFrame({"hour": range(24), "trips": data["hours"]})
    fig = px.bar(hd, x="hour", y="trips", color_discrete_sequence=[BLUE])
    fig.update_xaxes(tickmode="array", tickvals=list(range(0, 24, 3)),
                     ticktext=[f"{h % 12 or 12}{'am' if h < 12 else 'pm'}" for h in range(0, 24, 3)], title="")
    fig.update_layout(margin=dict(l=0, r=10, t=10, b=10), height=300)
    st.plotly_chart(fig)
with b:
    st.subheader("Do far-away stops get fewer buses?")
    st.caption("Each dot is a bus stop. Higher = more buses a day. Green = many buses, red = very few.")
    sc = pd.DataFrame(data["scatter"])
    if sc.empty:
        st.write("No stops match this selection.")
    else:
        fig = px.scatter(sc, x="km", y="trips", color="level", color_discrete_map=LEVEL_COLORS,
                         category_orders={"level": LEVELS}, labels={"km": "Distance from Anekal (km)", "trips": "Trips a day"})
        fig.update_layout(margin=dict(l=0, r=10, t=10, b=10), height=300, legend_title="")
        st.plotly_chart(fig)

c, d = st.columns(2)
with c:
    st.subheader("Busiest routes")
    st.caption("A longer bar means more bus trips a day. The code in brackets is the number on the bus.")
    st.plotly_chart(bars(data["top_routes"]))
with d:
    st.subheader("Where do buses end their journey?")
    st.caption("Share of trips by last stop. “Anekal” means buses coming back into town.")
    if data["destinations"]:
        dd = pd.DataFrame(data["destinations"], columns=["name", "trips"])
        fig = px.pie(dd, names="name", values="trips", hole=0.5)
        fig.update_layout(margin=dict(l=0, r=0, t=10, b=10), height=300)
        st.plotly_chart(fig)

e, f = st.columns(2)
with e:
    st.subheader("Buses per stop, by distance from the town centre")
    st.caption("Typical number of buses a day at a stop. Shows all areas together.")
    db = pd.DataFrame(DISTANCE_BANDS, columns=["band", "median"])
    fig = px.bar(db, x="band", y="median", text="median", color=db["median"] < 10,
                 color_discrete_map={True: RED, False: BLUE})
    fig.update_layout(showlegend=False, xaxis_title="", yaxis_title="", margin=dict(l=0, r=10, t=10, b=10), height=300)
    st.plotly_chart(fig)
with f:
    st.subheader("How well are the town’s stops served?")
    st.caption("High = 200+ trips a day, Medium = 50-199, Low = 10-49, Very low = under 10.")
    lv = pd.DataFrame(data["levels"], columns=["name", "stops"])
    fig = px.bar(lv, x="name", y="stops", text="stops", color="name", color_discrete_map=LEVEL_COLORS)
    fig.update_layout(showlegend=False, xaxis_title="", yaxis_title="", margin=dict(l=0, r=10, t=10, b=10), height=300)
    st.plotly_chart(fig)

st.divider()
st.subheader("In short, for your selection")
st.success(data["summary"])
st.markdown("#### What the numbers mean (Anekal town)")
st.markdown(
    "- Buses are concentrated in the town centre. The main Anekal stop alone has about 872 bus trips a day.\n"
    "- Service is uneven: 12 stops get 200 or more trips a day, but 23 stops get fewer than 10.\n"
    "- At 29 of the 59 town stops there is a gap of over an hour between buses at some point in the day.\n"
    "- Fewer buses run at midday and late night: about 79 trips at 10am, 34 around 1pm and only 14 at 10pm.\n"
    "- No direct bus goes to Electronic City or Hosur, so riders must change buses.")
st.markdown("#### Conclusion and suggestions")
st.markdown(
    "Buses serve Anekal’s centre and a few main roads well, but many nearby stops get very few. We suggest:\n"
    "- Add small feeder buses from lightly served stops to the town centre.\n"
    "- Add more buses at midday and late evening on the busy Majestic routes.\n"
    "- Start a direct bus from Anekal to Electronic City so people need not change buses.\n"
    "- Run buses to Bommasandra Metro more often to connect riders to the metro.")
st.caption("Trip = one bus journey. Stop = a place where a bus halts. Route = a bus number such as 356-Z. "
           "Data: community BMTC timetable (GTFS), one service day; not live tracking.")
