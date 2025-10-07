# App Setup and Run Instructions

## 1. Clone the Repository
```bash
git clone <repository_url>
cd <repository_folder>
```

## 2. Create and Activate Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

*(For Windows: `venv\Scripts\activate`)*

## 3. Install Dependencies
```bash
pip install -r requirements.txt
```

## 4. Run the Application
```bash
./uvicorn.run.sh
```

## 5. Test the Application
Open your browser and visit:
```
http://127.0.0.1:8000/
```

---
**Tip:** Make sure the `uvicorn.run.sh` script has executable permissions:
```bash
chmod +x uvicorn.run.sh
```

**Full setup script**
```bash
git clone https://github.com/magda-realnetworks/fuzzy-name-matching.git
cd fuzzy-name-matching
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
./uvicorn.run.sh
```
