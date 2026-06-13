# Steps to Create the GEO-MixQC GitHub Repository and Get a DOI

## Step 1: Create the repository on GitHub
1. Go to https://github.com/ and sign in with your account
2. Click the green "New" button (or go to https://github.com/new)
3. Repository name: `geo-mixqc`
4. Description: `Five-test algorithm for detecting mixed-normalization artifacts in public transcriptomic matrices`
5. Set to **Public**
6. Do NOT initialize with README (we already have one)
7. Click "Create repository"

## Step 2: Push the local code to GitHub
Open a terminal (Git Bash) and run:

```bash
cd /c/Users/yun/Desktop/geo-mixqc

# Initialize git
git init
git add .
git commit -m "Initial release: GEO-MixQC v1.0.0"

# Link to your GitHub repository (REPLACE YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/geo-mixqc.git
git branch -M main
git push -u origin main
```

## Step 3: Update pyproject.toml and README.md
After pushing, edit these two files and replace `YOUR_USERNAME` with your actual GitHub username:
- `pyproject.toml` line ~30-33: change `YOUR_USERNAME` to your actual username in all URLs
- `README.md` line ~24: change `YOUR_USERNAME` in the git clone command

Then commit and push the changes:
```bash
git add pyproject.toml README.md
git commit -m "Update repository URLs"
git push
```

## Step 4: Create a release and get a DOI via Zenodo
1. Go to https://github.com/YOUR_USERNAME/geo-mixqc/releases
2. Click "Create a new release"
3. Tag version: `v1.0.0`
4. Release title: `GEO-MixQC v1.0.0 — Initial Release`
5. Description: "First public release. Five-test mixed-normalization detection algorithm. Validated on 550 GPL570 datasets. See manuscript for details."
6. Click "Publish release"

7. Then go to https://zenodo.org/ and:
   - Sign in with your GitHub account
   - Go to https://zenodo.org/account/settings/github/
   - Find `geo-mixqc` in your repository list
   - Toggle the switch to ON
   - Go back to GitHub and create another release (or edit the existing one)
   - Zenodo will automatically create a DOI for your release
   - Copy the DOI badge markdown and add it to your README.md

## Step 5: Update the manuscript
After getting the DOI, update the manuscript:
- Replace `https://github.com/username/geo-mixqc` with your actual URL
- Replace `placeholder` DOI with the actual Zenodo DOI
