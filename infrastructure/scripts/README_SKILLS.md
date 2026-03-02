# Skills and Jobs Data Loader

This directory contains the data loader script for skill development programs and government job postings.

## Files

- `load_skills.py` - Main data loader script with sample data
- `README_SKILLS.md` - This documentation file

## Sample Data

The script includes:
- **10 Skill Development Programs** covering:
  - Technical skills (Electrician, Plumbing, Mobile Repair)
  - Vocational training (Retail, Beauty & Wellness, Tailoring, Hospitality)
  - Digital literacy (CCC, O Level)
  - Entrepreneurship development

- **10 Government Job Postings** including:
  - Engineering positions (Junior Engineer)
  - Administrative roles (Clerk, Office Assistant)
  - Security services (Police Constable, CAPF Sub Inspector)
  - Specialized positions (Teacher, Staff Nurse, Agriculture Extension Officer)
  - Banking and Railway jobs

## Usage

### Dry Run (Validation Only)
```bash
python infrastructure/scripts/load_skills.py --dry-run
```

### Load Both Programs and Jobs
```bash
python infrastructure/scripts/load_skills.py
```

### Load Only Skill Programs
```bash
python infrastructure/scripts/load_skills.py --type programs
```

### Load Only Job Postings
```bash
python infrastructure/scripts/load_skills.py --type jobs
```

### Custom Table Names and Region
```bash
python infrastructure/scripts/load_skills.py \
  --programs-table MySkillPrograms \
  --jobs-table MyJobPostings \
  --region ap-south-1
```

## Command Line Options

- `--type` - Data type to load: `programs`, `jobs`, or `both` (default: `both`)
- `--programs-table` - DynamoDB table name for skill programs (default: `SkillPrograms`)
- `--jobs-table` - DynamoDB table name for job postings (default: `JobPostings`)
- `--region` - AWS region (default: `us-east-1`)
- `--dry-run` - Validate data without inserting into DynamoDB

## Requirements

- Python 3.8+
- boto3
- pydantic
- AWS credentials configured
- DynamoDB tables created (see infrastructure/README.md)

## Data Validation

The script validates all data before insertion:
- Skill programs are validated against the `SkillProgram` model
- Job postings are validated against the `JobPosting` model
- Invalid records are logged and skipped
- Summary report shows success/failure counts

## Sample Data Details

### Skill Programs Coverage
- **States**: Maharashtra, Karnataka, Delhi, UP, Tamil Nadu, Gujarat, West Bengal, Rajasthan, Bihar
- **Categories**: Technical, Vocational, Digital, Entrepreneurship
- **Duration**: 6-52 weeks
- **Cost**: Free to ₹5,000
- **Providers**: NSDC, DDU-GKY, NIELIT, Sector Skill Councils, RSETI

### Job Postings Coverage
- **States**: All India and state-specific positions
- **Departments**: PWD, SSC, Railways, Police, Education, UPSC, PSC, Banking, Health, Agriculture
- **Qualifications**: 10th pass to Bachelor's degree
- **Salary Range**: ₹18,000 - ₹1,42,400 per month
- **Vacancies**: 25-1000 positions per posting
