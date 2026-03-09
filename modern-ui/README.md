# BharatSahayak - Modern UI

A clean, modern, responsive web application for AI-powered government scheme discovery.

## Features

- Modern SaaS-style dashboard design
- Fully responsive (mobile, tablet, desktop)
- Vanilla HTML, CSS, JavaScript (no frameworks)
- Blue/Indigo color theme
- Smooth animations and transitions
- Local storage for user data and saved schemes
- **3,400+ real government schemes** from CSV dataset

## Pages

1. **index.html** - Landing page with hero, features, and how-it-works
2. **login.html** - Authentication page with login and guest access
3. **profile-setup.html** - First-time user profile setup
4. **dashboard.html** - Main dashboard with AI search and recommendations
5. **search.html** - Advanced search with filters (category, level, state)
6. **details.html** - Detailed scheme information
7. **saved.html** - Bookmarked schemes

## Structure

```
modern-ui/
├── index.html
├── login.html
├── profile-setup.html
├── dashboard.html
├── search.html
├── details.html
├── saved.html
├── css/
│   └── styles.css
└── js/
    ├── app.js
    ├── schemes-data.js (auto-generated)
    └── convert-csv.js
```

## Setup

1. Convert CSV dataset to JavaScript:
```bash
node js/convert-csv.js
```

2. Open `index.html` in a browser or deploy to S3:
```bash
bash deploy.sh
```

## Usage

1. Open `index.html` in a browser
2. Click "Try as Guest" or "Login"
3. Complete profile setup (first-time users)
4. Explore dashboard and search 3,400+ schemes

## Data Integration

The UI now uses your real dataset from `data/updated_data.csv`:
- 3,400+ government schemes
- Categories: Education, Health, Agriculture, Business, Social Welfare, etc.
- Levels: Central and State schemes
- Full details: eligibility, benefits, documents, application steps

## Key Features

- Collapsible sidebar navigation
- AI-powered search bar
- Scheme filtering by category, level, state
- Save/bookmark schemes
- Responsive mobile menu
- Local storage persistence
- Real government scheme data

## Design Highlights

- Clean card-based layouts
- Smooth hover effects
- Professional color scheme (Indigo primary)
- Accessible form controls
- Mobile-first responsive design
