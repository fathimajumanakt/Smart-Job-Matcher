
import re
import requests
import streamlit as st

from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed


# =====================================================
# PAGE CONFIGURATION
# =====================================================

st.set_page_config(
    page_title="Smart Job Matcher",
    page_icon="🎯",
    layout="wide"
)


# =====================================================
# CUSTOM BLACK AND BLUE DESIGN
# =====================================================

st.markdown("""
<style>

.stApp {
    background-color: #080d18;
    color: white;
}

[data-testid="stSidebar"] {
    background-color: #101a2d;
}

h1, h2, h3 {
    color: #38bdf8 !important;
}

.stButton > button {
    background-color: #0879df;
    color: white;
    border-radius: 9px;
    border: none;
    font-weight: bold;
}

.stButton > button:hover {
    background-color: #1597ff;
    color: white;
}

.stProgress > div > div > div {
    background-color: #168cff;
}

.job-card {
    background-color: #111d32;
    border: 1px solid #23456e;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 15px;
}

.metric-card {
    background-color: #111d32;
    border: 1px solid #23456e;
    padding: 18px;
    border-radius: 12px;
    text-align: center;
}

div[data-testid="stMetricValue"] {
    color: #38bdf8;
}

</style>
""", unsafe_allow_html=True)


# =====================================================
# HEADER
# =====================================================

st.title("🎯 Smart Job Matcher")

st.caption(
    "Discover job opportunities based on your skills, "
    "preferred job roles, experience and location."
)

st.divider()


# =====================================================
# API CONFIGURATION
# =====================================================

API_URL = "https://jobsforceindia.com/api/public/v1/jobs"

HEADERS = {
    "User-Agent": "SmartJobMatcher/3.0"
}

TIMEOUT = 20

PER_PAGE = 20

MAX_PAGES = 10


# =====================================================
# JOB CATEGORIES
# =====================================================

JOB_CATEGORIES = {

    "All Jobs": [
        "Data Analyst",
        "Business Analyst",
        "Software Developer",
        "Python Developer",
        "Accountant",
        "HR Executive",
        "Marketing Executive",
        "Sales Executive",
        "Customer Support Executive",
        "Graphic Designer",
        "Project Manager",
        "Business Development Executive"
    ],

    "Data & Analytics": [
        "Data Analyst",
        "Junior Data Analyst",
        "Business Analyst",
        "Reporting Analyst",
        "Data Scientist",
        "Power BI Developer",
        "Data Analytics Intern",
        "Data Analyst Intern"
    ],

    "IT & Software": [
        "Software Developer",
        "Python Developer",
        "Java Developer",
        "Web Developer",
        "SQL Developer",
        "Frontend Developer",
        "Backend Developer",
        "Software Tester"
    ],

    "Finance & Accounting": [
        "Accountant",
        "Accounts Executive",
        "Financial Analyst",
        "Finance Assistant",
        "Junior Accountant"
    ],

    "Marketing": [
        "Digital Marketing Executive",
        "Marketing Executive",
        "SEO Analyst",
        "Social Media Executive",
        "Marketing Intern"
    ],

    "HR & Administration": [
        "HR Executive",
        "HR Assistant",
        "Recruitment Executive",
        "Office Administrator"
    ],

    "Business & Management": [
        "Business Associate",
        "Business Development Executive",
        "Operations Executive",
        "Management Trainee"
    ],

    "Sales & Customer Support": [
        "Sales Executive",
        "Sales Manager",
        "Customer Support Executive",
        "Customer Service Representative"
    ],

    "Design": [
        "Graphic Designer",
        "UI UX Designer",
        "Web Designer",
        "Creative Designer"
    ],

    "Internships": [
        "Data Analytics Intern",
        "Software Developer Intern",
        "Marketing Intern",
        "HR Intern",
        "Python Developer Intern"
    ]
}


# =====================================================
# RELATED JOB POSITIONS
# =====================================================

RELATED_ROLES = {

    "Data Analyst": [
        "Data Analyst",
        "Junior Data Analyst",
        "Reporting Analyst",
        "Business Analyst",
        "Power BI Developer",
        "Data Analytics Intern",
        "Data Analyst Intern"
    ],

    "Junior Data Analyst": [
        "Junior Data Analyst",
        "Data Analyst",
        "Reporting Analyst",
        "Data Analytics Intern"
    ],

    "Business Analyst": [
        "Business Analyst",
        "Junior Business Analyst",
        "Data Analyst",
        "Business Associate",
        "Reporting Analyst"
    ],

    "Python Developer": [
        "Python Developer",
        "Junior Python Developer",
        "Software Developer",
        "Python Developer Intern"
    ],

    "Software Developer": [
        "Software Developer",
        "Junior Software Developer",
        "Python Developer",
        "Web Developer"
    ],

    "Accountant": [
        "Accountant",
        "Junior Accountant",
        "Accounts Executive",
        "Finance Assistant"
    ],

    "HR Executive": [
        "HR Executive",
        "HR Assistant",
        "Recruitment Executive"
    ],

    "Marketing Executive": [
        "Marketing Executive",
        "Digital Marketing Executive",
        "SEO Analyst",
        "Social Media Executive"
    ],

    "Sales Executive": [
        "Sales Executive",
        "Sales Manager",
        "Business Development Executive"
    ]
}


# =====================================================
# LOCATION OPTIONS
# =====================================================

LOCATION_OPTIONS = [
    "All India",
    "Kerala",
    "Kozhikode",
    "Malappuram",
    "Kochi",
    "Kannur",
    "Thrissur",
    "Thiruvananthapuram",
    "Bengaluru",
    "Chennai",
    "Hyderabad",
    "Mumbai",
    "Pune",
    "Delhi",
    "Other City",
    "Remote"
]


CITY_ALIASES = {

    "kozhikode": ["kozhikode", "calicut"],

    "malappuram": ["malappuram"],

    "kochi": ["kochi", "cochin", "ernakulam"],

    "kannur": ["kannur", "cannanore"],

    "thiruvananthapuram": [
        "thiruvananthapuram",
        "trivandrum"
    ],

    "thrissur": ["thrissur", "trichur"],

    "bengaluru": ["bengaluru", "bangalore"],

    "mumbai": ["mumbai", "bombay"]
}


# =====================================================
# HELPER FUNCTIONS
# =====================================================

def clean(value):

    if value is None:
        return ""

    if isinstance(value, dict):

        return " ".join(
            clean(v) for v in value.values()
        )

    if isinstance(value, list):

        return " ".join(
            clean(v) for v in value
        )

    return str(value).strip()


def normalize(value):

    return re.sub(
        r"[^a-z0-9]+",
        " ",
        clean(value).lower()
    ).strip()


def get_title(job):

    return clean(
        job.get("title")
        or job.get("job_title")
        or job.get("role")
        or "Untitled Job"
    )


def get_company(job):

    hiring = job.get("hiring", {})

    company = ""

    if isinstance(hiring, dict):

        company = clean(
            hiring.get("company")
            or hiring.get("company_name")
            or hiring.get("name")
        )

    company = company or clean(
        job.get("company")
        or job.get("company_name")
        or job.get("employer")
    )

    return company or "Company not disclosed"


def get_location(job):

    location = job.get("location", {})

    if isinstance(location, dict):

        city = clean(
            location.get("city")
            or job.get("city")
        )

        state = clean(
            location.get("state")
            or job.get("state")
        )

        country = clean(
            location.get("country")
        )

        mode = clean(
            location.get("work_mode")
            or job.get("work_mode")
            or job.get("workplace_type")
        )

        display = ", ".join(
            x for x in [city, state, country] if x
        )

        if not display:

            display = clean(location.get("name"))

        remote = (
            location.get("remote") is True
            or "remote" in normalize(mode)
            or "work from home" in normalize(mode)
            or "remote" in normalize(display)
        )

    else:

        city = clean(job.get("city"))

        state = clean(job.get("state"))

        display = clean(location)

        mode = clean(
            job.get("work_mode")
            or job.get("workplace_type")
        )

        remote = (
            "remote" in normalize(display)
            or "remote" in normalize(mode)
            or "work from home" in normalize(mode)
        )

    if not display:

        display = "Location not specified"

    return city, state, display, remote


def get_description(job):

    fields = [

        job.get("summary"),
        job.get("description"),
        job.get("skills"),
        job.get("requirements"),
        job.get("responsibilities"),
        job.get("qualifications"),
        job.get("category"),
        job.get("experience")

    ]

    return normalize(
        " ".join(clean(x) for x in fields)
    )


def extract_jobs(data):

    if isinstance(data, list):

        return data

    if not isinstance(data, dict):

        return []

    for key in ["jobs", "results", "data", "items"]:

        value = data.get(key)

        if isinstance(value, list):

            return value

        if isinstance(value, dict):

            for nested in [
                "jobs",
                "results",
                "items"
            ]:

                if isinstance(value.get(nested), list):

                    return value[nested]

    return []


# =====================================================
# API REQUEST
# =====================================================

def fetch_page(params):

    try:

        response = requests.get(
            API_URL,
            params=params,
            headers=HEADERS,
            timeout=TIMEOUT
        )

        response.raise_for_status()

        data = response.json()

        jobs = extract_jobs(data)

        return jobs, None

    except requests.exceptions.Timeout:

        return [], "API request timed out."

    except requests.exceptions.HTTPError as error:

        return [], (
            f"API HTTP error: {error}"
        )

    except requests.exceptions.RequestException as error:

        return [], str(error)

    except ValueError:

        return [], "Invalid API response."


# =====================================================
# PAGINATION
# =====================================================

def search_one_role(role, city=""):

    all_jobs = []

    errors = []

    for page in range(1, MAX_PAGES + 1):

        params = {

            "q": role,

            "page": page,

            "per_page": PER_PAGE

        }

        if city:

            params["city"] = city

        jobs, error = fetch_page(params)

        if error:

            errors.append(error)

            break

        if not jobs:

            break

        all_jobs.extend(jobs)

        if len(jobs) < PER_PAGE:

            break

    return all_jobs, errors


# =====================================================
# SEARCH MULTIPLE JOB POSITIONS
# =====================================================

def search_multiple_roles(roles, city=""):

    all_jobs = []

    errors = []

    progress = st.progress(
        0,
        text="Preparing job searches..."
    )

    completed = 0

    with ThreadPoolExecutor(
        max_workers=4
    ) as executor:

        futures = {

            executor.submit(
                search_one_role,
                role,
                city
            ): role

            for role in roles

        }

        for future in as_completed(futures):

            try:

                jobs, job_errors = future.result()

                all_jobs.extend(jobs)

                errors.extend(job_errors)

            except Exception as error:

                errors.append(str(error))

            completed += 1

            progress.progress(
                completed / len(roles),
                text=f"Searching positions: {completed}/{len(roles)}"
            )

    progress.empty()

    return all_jobs, errors


# =====================================================
# REMOVE DUPLICATES
# =====================================================

def remove_duplicates(jobs):

    unique = {}

    for job in jobs:

        job_id = clean(
            job.get("id")
            or job.get("job_id")
        )

        if job_id:

            key = job_id

        else:

            key = (
                normalize(get_title(job))
                + normalize(get_company(job))
                + normalize(get_location(job)[2])
            )

        if key not in unique:

            unique[key] = job

    return list(unique.values())


# =====================================================
# LOCATION MATCHING
# =====================================================

def location_matches(job, selected):

    city, state, display, remote = get_location(job)

    selected = normalize(selected)

    city_n = normalize(city)

    state_n = normalize(state)

    display_n = normalize(display)

    if selected == "remote":

        return remote

    if selected == "all india":

        return not remote

    if selected == "kerala":

        return (
            "kerala" in state_n
            or "kerala" in display_n
        )

    aliases = CITY_ALIASES.get(
        selected,
        [selected]
    )

    for alias in aliases:

        alias_n = normalize(alias)

        if (
            alias_n == city_n
            or alias_n in display_n
        ):

            return not remote

    return False


# =====================================================
# SKILL MATCHING
# =====================================================

def calculate_skill_match(job, skills):

    if not skills:

        return 0, [], []

    description = get_description(job)

    matched = []

    missing = []

    for skill in skills:

        skill_n = normalize(skill)

        if not skill_n:

            continue

        pattern = (
            r"(?<![a-z0-9])"
            + re.escape(skill_n)
            + r"(?![a-z0-9])"
        )

        if re.search(pattern, description):

            matched.append(skill)

        else:

            missing.append(skill)

    total = len(matched) + len(missing)

    score = round(
        len(matched) / total * 100
    ) if total else 0

    return score, matched, missing


# =====================================================
# JOB DETAILS
# =====================================================

def get_salary(job):

    salary = job.get("salary", "")

    if isinstance(salary, dict):

        display = clean(
            salary.get("display")
            or salary.get("range")
            or salary.get("text")
        )

        if display:

            return display

        minimum = (
            salary.get("min_monthly")
            or salary.get("min")
        )

        maximum = (
            salary.get("max_monthly")
            or salary.get("max")
        )

        if minimum and maximum:

            return f"₹{minimum} - ₹{maximum}"

        if minimum or maximum:

            return f"₹{minimum or maximum}"

    return clean(salary) or "Not disclosed"


def get_experience(job):

    experience = job.get("experience", "")

    if isinstance(experience, dict):

        experience = (
            experience.get("display")
            or experience.get("text")
            or experience.get("required")
            or ""
        )

    return clean(experience) or "Not specified"


def safe_url(value):

    value = clean(value)

    if value.startswith("//"):

        value = "https:" + value

    parsed = urlparse(value)

    if (
        parsed.scheme in ["http", "https"]
        and parsed.netloc
    ):

        return value

    return ""


# =====================================================
# EXPERIENCE FILTER
# =====================================================

def experience_matches(job, selected):

    if selected == "All Experience":

        return True

    text = normalize(
        get_experience(job)
        + " "
        + get_description(job)
    )

    if selected == "Fresher":

        return (
            "fresher" in text
            or "entry level" in text
            or "0 year" in text
            or "0 1 year" in text
            or "no experience" in text
        )

    if selected == "Internship":

        return "intern" in text

    if selected == "0-1 Years":

        return (
            "0 1 year" in text
            or "0 2 years" in text
            or "fresher" in text
            or "entry level" in text
        )

    if selected == "1-3 Years":

        return (
            "1 3 years" in text
            or "1 2 years" in text
            or "2 3 years" in text
        )

    if selected == "3-5 Years":

        return (
            "3 5 years" in text
            or "3 4 years" in text
            or "4 5 years" in text
        )

    return True


# =====================================================
# JOB CARD
# =====================================================

def display_job(job, skills):

    st.markdown(
        '<div class="job-card">',
        unsafe_allow_html=True
    )

    st.subheader(
        "💼 " + get_title(job)
    )

    st.write(
        "**Company:**",
        get_company(job)
    )

    city, state, location, remote = get_location(job)

    st.write(
        "**Location:**",
        location
    )

    st.write(
        "**Work Mode:**",
        "Remote" if remote else "On-site / Not specified"
    )

    st.write(
        "**Salary:**",
        get_salary(job)
    )

    st.write(
        "**Experience:**",
        get_experience(job)
    )

    score, matched, missing = calculate_skill_match(
        job,
        skills
    )

    st.progress(
        score / 100,
        text=f"Estimated Skill Match: {score}%"
    )

    if matched:

        st.success(
            "Matching Skills: "
            + ", ".join(matched)
        )

    if missing:

        st.warning(
            "Skills not found in listing: "
            + ", ".join(missing)
        )

    summary = clean(
        job.get("summary")
        or job.get("description")
    )

    if summary:

        st.write(
            summary[:500]
            + ("..." if len(summary) > 500 else "")
        )

    job_url = safe_url(
        job.get("url")
        or job.get("browse_url")
    )

    apply_url = safe_url(
        job.get("apply_url")
        or job.get("application_url")
    )

    col1, col2 = st.columns(2)

    with col1:

        if job_url:

            st.link_button(
                "🔎 View Job",
                job_url,
                use_container_width=True
            )

    with col2:

        if apply_url:

            st.link_button(
                "📩 Apply Now",
                apply_url,
                use_container_width=True
            )

        elif job_url:

            st.link_button(
                "Apply / Details",
                job_url,
                use_container_width=True
            )

    st.markdown(
        "</div>",
        unsafe_allow_html=True
    )

    st.write("")


# =====================================================
# SIDEBAR
# =====================================================

with st.sidebar:

    st.title("🔎 Job Search")

    st.caption(
        "Find opportunities matching your profile."
    )

    category = st.selectbox(
        "Job Category",
        list(JOB_CATEGORIES.keys())
    )

    selected_role = st.selectbox(
        "Job Position",
        JOB_CATEGORIES[category]
    )

    custom_role = st.text_input(
        "Custom Job Position",
        placeholder="Example: Data Analyst"
    )

    st.divider()

    selected_location = st.selectbox(
        "Preferred Location",
        LOCATION_OPTIONS
    )

    custom_city = ""

    if selected_location == "Other City":

        custom_city = st.text_input(
            "Enter City",
            placeholder="Example: Bengaluru"
        )

    st.divider()

    skills_input = st.text_area(
        "Your Skills",
        value="Excel, SQL, Python, Power BI",
        height=100
    )

    experience_filter = st.selectbox(
        "Experience Level",
        [
            "All Experience",
            "Fresher",
            "Internship",
            "0-1 Years",
            "1-3 Years",
            "3-5 Years"
        ]
    )

    st.divider()

    search_button = st.button(
        "🚀 Find Matching Jobs",
        type="primary",
        use_container_width=True
    )


# =====================================================
# MAIN SEARCH PROCESS
# =====================================================

if search_button:

    role = custom_role.strip() or selected_role

    location = (
        custom_city.strip()
        if selected_location == "Other City"
        else selected_location
    )

    if not role:

        st.error(
            "Please enter a job position."
        )

    elif (
        selected_location == "Other City"
        and not custom_city.strip()
    ):

        st.error(
            "Please enter your preferred city."
        )

    else:

        skills = [
            x.strip()
            for x in skills_input.split(",")
            if x.strip()
        ]

        # Related positions

        roles = RELATED_ROLES.get(
            role,
            [role]
        )

        # Always include the selected position

        if role not in roles:

            roles.insert(0, role)

        # Search API

        with st.spinner(
            "Finding available job opportunities..."
        ):

            api_city = ""

            if location not in [
                "All India",
                "Kerala",
                "Remote"
            ]:

                api_city = location

            # For Kerala, search using its state name.
            # For Remote, use a remote keyword.

            if location == "Kerala":

                roles = [
                    r + " in Kerala"
                    for r in roles
                ]

            elif location == "Remote":

                roles = [
                    r + " remote"
                    for r in roles
                ]

            jobs, errors = search_multiple_roles(
                roles,
                api_city
            )

            jobs = remove_duplicates(jobs)

            local_results = []

            remote_results = []

            for job in jobs:

                city, state, display, remote = get_location(job)

                if remote:

                    remote_results.append(job)

                elif location == "Remote":

                    continue

                elif location_matches(job, location):

                    local_results.append(job)

            # Apply experience filter

            local_results = [
                job for job in local_results
                if experience_matches(job, experience_filter)
            ]

            remote_results = [
                job for job in remote_results
                if experience_matches(job, experience_filter)
            ]

            # Sort by skill match

            local_results.sort(
                key=lambda job: calculate_skill_match(
                    job,
                    skills
                )[0],
                reverse=True
            )

            remote_results.sort(
                key=lambda job: calculate_skill_match(
                    job,
                    skills
                )[0],
                reverse=True
            )

            # Save results

            st.session_state["local_results"] = local_results

            st.session_state["remote_results"] = remote_results

            st.session_state["search_role"] = role

            st.session_state["search_location"] = location

            st.session_state["search_skills"] = skills

            st.session_state["search_errors"] = errors

            st.session_state["searched"] = True

            st.session_state["total_retrieved"] = len(jobs)


# =====================================================
# DISPLAY RESULTS
# =====================================================

if st.session_state.get("searched"):

    local_results = st.session_state.get(
        "local_results",
        []
    )

    remote_results = st.session_state.get(
        "remote_results",
        []
    )

    current_role = st.session_state.get(
        "search_role",
        ""
    )

    current_location = st.session_state.get(
        "search_location",
        ""
    )

    current_skills = st.session_state.get(
        "search_skills",
        []
    )

    st.subheader(
        f"🎯 Job Results for {current_role}"
    )

    st.caption(
        f"Preferred Location: {current_location}"
    )

    # Dashboard metrics

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Local Jobs",
            len(local_results)
        )

    with col2:

        st.metric(
            "Remote Jobs",
            len(remote_results)
        )

    with col3:

        st.metric(
            "Total Jobs Retrieved",
            st.session_state.get(
                "total_retrieved",
                0
            )
        )

    st.divider()

    # Tabs

    local_tab, remote_tab = st.tabs(
        [
            f"📍 Local Jobs ({len(local_results)})",
            f"🌐 Remote Jobs ({len(remote_results)})"
        ]
    )

    with local_tab:

        if local_results:

            for job in local_results:

                display_job(
                    job,
                    current_skills
                )

        else:

            st.warning(
                "No matching local vacancies were found."
            )

            st.info(
                "Try All India or another city. "
                "Results depend on currently available API listings."
            )

    with remote_tab:

        if remote_results:

            for job in remote_results:

                display_job(
                    job,
                    current_skills
                )

        else:

            st.info(
                "No matching remote vacancies were found."
            )

    # API errors

    errors = st.session_state.get(
        "search_errors",
        []
    )

    if errors:

        with st.expander("API Notices"):

            for error in errors:

                st.write(error)


else:

    st.info(
        "👈 Select your preferred job position, "
        "location and skills, then click Find Matching Jobs."
    )

    st.markdown("""
    ### ✨ What you can do here

    - Search different job positions.
    - Discover opportunities in different cities.
    - Find remote job opportunities.
    - Compare your skills with job requirements.
    - View job descriptions and application links.

    """)


# =====================================================
# FOOTER
# =====================================================

st.divider()

st.caption(
    "Smart Job Matcher | Machine Learning Project"
)

st.caption(
    "Job listings are retrieved from JobsForce India. "
    "Availability depends on the external API. "
    "Skill match scores are estimates based on "
    "the information available in each job description."
)
