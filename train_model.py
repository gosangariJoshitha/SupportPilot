import pandas as pd
from sklearn.model_selection import train_test_split 
from sklearn.feature_extraction.text import TfidfVectorizer 
from sklearn.linear_model import LogisticRegression, SGDClassifier
from sklearn.svm import LinearSVC
from sklearn.naive_bayes import MultinomialNB, ComplementNB
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report, confusion_matrix
import joblib
import os
import time
import json
import matplotlib.pyplot as plt
import seaborn as sns

def train_and_save_model():
    data = {
        "ticket": [
            # Network
            "WiFi is not working", "Internet connection is very slow", "Cannot connect to the office wifi", 
            "Network drops frequently", "No internet access on my laptop", "The router seems to be offline", 
            "Ethernet port is not working", "Wifi signal is too weak in the conference room", 
            "Local network file share is unreachable", "Slow network speeds during downloads", 
            "My wifi is disconnected", "No network connection", "Internet is down",  
            "The LAN is not working", "Wifi keeps disconnecting", "Can't access the internet", 
            "Network speed is terrible", "Ping is very high", "Ethernet cable is broken", 
            "Cannot reach network drive", 
            "Router needs reboot", "Lost connection to the network", "WiFi password changed", "Network outage", "Bad internet connection", 
            "Network switch is down", "Can't ping the default gateway", "No internet", "WiFi password doesn't work", "Cannot connect to WiFi", 
            "LAN cable is unplugged", "Ethernet not detected", "Wifi is super slow", "Internet connection lost", "Network drive not mounting", 
            "IP address conflict", "DHCP server not responding", "DNS resolution failed", "Proxy server error", "Firewall blocking internet", 
            
            # VPN
            "VPN is not connecting", "Unable to access company VPN", "Cisco AnyConnect VPN error", 
            "VPN connection keeps dropping", "Cannot access internal sites while on VPN", 
            "VPN authentication failed", "Getting timeout error when connecting to VPN", 
            "VPN is too slow when working from home", "How do I install the VPN client?", 
            "VPN is blocked on my current network", "VPN client is crashing", "VPN doesn't work", 
            "I cannot connect to the VPN", "VPN keeps disconnecting every 5 minutes", 
            "GlobalProtect VPN fails", "Need help with VPN access", "VPN login invalid", 
            "VPN server unreachable", "Can't access intranet without VPN", "VPN configuration error", 
            "VPN tunnel collapsed", "VPN software update needed", "Cannot ping over VPN", "VPN is dropping my connection", "VPN error code 404", 
            "VPN timeout", "Cannot connect to AnyConnect", "GlobalProtect is disconnected", "VPN requires multifactor authentication", "VPN tunnel failed", 
            "Cannot reach internal network over VPN", "VPN IP address not assigned", "VPN client needs update", "VPN connection refused", "VPN credentials rejected", 
            "VPN is blocking local network", "VPN speed is very slow", "VPN keeps reconnecting", "VPN profile missing", "VPN portal is down", 

            # Password
            "I forgot my password", "Please reset my password", "My account is locked out", 
            "Need a password reset for my email", "Windows login password is not working", 
            "Cannot log in, says invalid credentials", "How do I change my password?", 
            "SSO login is failing", "Active directory account locked", "Need to reset admin password", 
            "Forgot my login password", "Password expired", "Need help resetting password", 
            "Locked out of my account", "Reset my domain password", "Password isn't working", 
            "Invalid username or password", "Unlock my account", "AD password reset", "Change password request", 
            "Reset credentials for active directory", "I need to update my password", "Wrong password entered", "Password recovery link", "Cannot authenticate user", 
            "Reset active directory password", "Windows password expired", "SSO authentication failed", "Need new password", "Forgot my email password", 
            "Unlock my windows account", "Password reset link expired", "Cannot remember my password", "Change my login password", "Account locked after too many attempts", 
            "Need temporary password", "Password doesn't meet requirements", "MFA token out of sync for login", "Reset my domain credentials", "Help me reset my password", 

            # Software
            "Install Microsoft Office", "Application installation required", "Excel is crashing on startup", 
            "Need license for Adobe Acrobat", "Zoom is not updating", "Cannot open PDF files", 
            "Browser keeps crashing", "Need help installing Visual Studio", 
            "Antivirus software is showing an error", "Outlook is not sending emails", 
            "Word is frozen", "Teams is not loading", "Application is crashing",  
            "Need software license", "Install Chrome browser", "Software update failed", 
            "Cannot uninstall program", "App is unresponsive", "Error opening application", "Software is very slow", 
            "Photoshop is missing", "Slack won't open anymore", "Need to install zoom app", "Software license has expired", "Browser is extremely slow", 
            "Install Adobe Photoshop", "Word is crashing", "Excel macro error", "Cannot open Slack", "Zoom update failed", 
            "Need a license for IntelliJ", "Browser is not launching", "Teams audio not working", "Application license expired", "Software is freezing", 
            "Cannot install updates", "Uninstall unused software", "Requesting Microsoft Project", "App is not responding", "Error in the software application", 

            # Hardware
            "Laptop keyboard is not working", "Monitor display is not working", "Mouse is broken", 
            "Need a new charger for my laptop", "Printer is out of toner", "Laptop battery drains too fast", 
            "Screen is flickering", "Headset microphone is not picking up audio", "Need a docking station", 
            "Hard drive is making a clicking noise", "My screen is cracked", "Keyboard is missing keys", 
            "Laptop won't turn on", "Mouse is double clicking", "Need replacement battery", 
            "Printer paper jam", "Speaker has no sound", "Webcam is not working", "USB port broken", "Need a new mouse", 
            "RAM replacement needed", "Touchpad is not responding", "Headphones are broken", "Monitor has no video signal", "Laptop fan is very loud", 
            "Monitor is blank", "Keyboard is typing double letters", "Mouse scroll wheel broken", "Laptop battery dead", "Printer is making weird noises", 
            "Need a replacement charger", "Docking station not working", "Webcam image is blurry", "Headset earpad broken", "Microphone is muted hardware", 
            "USB drive not recognized", "Laptop hinges are broken", "Screen has dead pixels", "Need a second monitor", "Motherboard failure", 

            # System
            "My entire production server is down", "The client meeting system stopped working", 
            "Database server is unreachable", "Application deployment failed in production", 
            "System is out of memory", "High CPU usage on the main server", 
            "Web server is returning 500 errors", "Cannot restart the background service", 
            "Backup job failed last night", "Disk space is full on the server", 
            "Server is crashing", "Database connection lost", "Deployment pipeline failed", 
            "Out of memory error", "CPU is at 100%", "Service is unresponsive", 
            "Server reboot required", "System crash", "Error 502 bad gateway", "Backup is failing", 
            "Storage is completely full", "Kernel panic on boot", "Blue screen of death on server", "System restart needed urgently", "Server offline entirely", 
            "Production database is down", "Server rack lost power", "Kubernetes cluster unresponsive", "High memory usage on server", "CPU usage at 99%", 
            "Service stopped working on production", "Error 503 Service Unavailable", "Deployment pipeline is broken", "System backup failed", "Hard drive failure on server", 
            "Linux kernel panic", "IIS server not starting", "Out of memory on the host", "VM is not booting", "Active Directory server offline",
            # New additional Network
            "Cannot access external websites", "Router is blinking red", "DNS server is not responding", "IP address conflict detected", "No network access",
            "Wifi signal keeps dropping out", "Cannot connect to the hotel wifi", "Corporate network is denying access", "Slow upload speeds", "Ethernet port is dead",
            # New additional VPN
            "VPN authentication timeout", "GlobalProtect gateway not found", "Cisco AnyConnect installation failed", "VPN keeps asking for 2FA", "Cannot ping database over VPN",
            "Split tunneling is not working", "VPN disconnects when screen locks", "VPN client is outdated", "Cannot reach file server on VPN", "VPN connection is extremely unstable",
            # New additional Password
            "Need my LDAP password reset", "SSO token expired", "Cannot login to Okta", "Windows PIN is blocked", "Forgot my bitlocker recovery key",
            "Authenticator app lost sync", "Account is disabled", "Require admin rights for local account", "Temporary password is not working", "My credentials are not accepted",
            # New additional Software
            "VS Code is crashing", "Need visual studio 2022 license", "Docker desktop won't start", "Adobe reader update failed", "Firefox is completely frozen",
            "Slack keeps restarting", "Microsoft Project installation required", "Need access to Figma", "Anti-virus scan is stuck", "Office 365 needs repair",
            # New additional Hardware
            "Laptop screen is completely black", "External monitor not detected", "Keyboard spacebar is stuck", "Mouse cursor is jumping", "USB-C dock is not charging laptop",
            "Webcam shows a green screen", "Microphone has lots of static", "Printer is out of ink", "Laptop overheats and shuts down", "Power supply is making a buzzing sound",
            # New additional System
            "Redis cache server is down", "Elasticsearch cluster is red", "Web application is throwing 500", "Nginx is returning 502 bad gateway", "Cron job failed to execute",
            "Disk quota exceeded on server", "Main production database is locked", "AWS EC2 instance is unreachable", "High disk I/O on database server", "SSL certificate expired",
            # Extra additional Network
            "Cannot access the shared drive on network", "Intermittent internet connection drops", "WiFi keeps prompting for password", "Network is unreachable", "Default gateway is not responding",
            "Switch port is flapping", "BGP route is down", "VPN client cannot find network", "DNS cache is corrupted", "Unable to resolve hostname",
            # Extra additional VPN
            "VPN connection timed out after 30 seconds", "Corporate VPN is blocking my local printer", "AnyConnect profile is corrupted", "VPN Gateway is not reachable", "Cannot authenticate to VPN server",
            "MFA prompt not appearing for VPN", "GlobalProtect stuck on connecting", "VPN IP address is banned", "Cannot RDP over VPN", "VPN is dropping packets",
            # Extra additional Password
            "Forgot my pin code for windows", "Domain account locked out by admin", "Password reset email not arriving", "Cannot login after password change", "MFA device lost need reset",
            "Password complexity requirements not met", "Active directory sync delayed for password", "Cannot sign into Office 365", "Need my Azure AD password reset", "Local admin password required",
            # Extra additional Software
            "Outlook search is not working", "Cannot export to PDF from Word", "Teams screen share is black", "Browser extension is crashing", "Java update required to run app",
            "Python environment is broken", "Cannot launch IntelliJ IDEA", "Git is throwing authentication error", "Zoom audio is completely muted", "Excel is taking forever to open",
            # Extra additional Hardware
            "Laptop battery is swelling", "Keys on the keyboard are sticky", "Monitor stand is broken", "USB ports are not recognizing devices", "Headset cord is frayed",
            "Laptop is making a loud grinding noise", "Screen is completely shattered", "Mouse laser is not tracking", "Need a replacement HDMI cable", "Printer is out of paper",
            # Extra additional System
            "PostgreSQL database is corrupt", "Server disk space is 100% full", "Apache server is down", "Service failed to start on boot", "Out of memory killer killed the process",
            "System is completely unresponsive", "Datacenter power failure", "Cannot SSH into production server", "System logs are filling up disk", "Critical security patch failed"
        ],
        "category": (
            ["Network"] * 40 + ["VPN"] * 40 + ["Password"] * 40 + ["Software"] * 40 + ["Hardware"] * 40 + ["System"] * 40 +
            ["Network"] * 10 + ["VPN"] * 10 + ["Password"] * 10 + ["Software"] * 10 + ["Hardware"] * 10 + ["System"] * 10 +
            ["Network"] * 10 + ["VPN"] * 10 + ["Password"] * 10 + ["Software"] * 10 + ["Hardware"] * 10 + ["System"] * 10
        )
    }

    print("Loading existing ticket dataset from train_model.py...")
    df = pd.DataFrame(data)
    
    total_tickets = len(df)
    print(f"Total tickets: {total_tickets}")
    for cat, count in df['category'].value_counts().items():
        print(f"{cat}: {count}")
    print()

    X = df["ticket"]
    y = df["category"]

    print("Splitting dataset...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.15, stratify=y, random_state=42 
    )

    print("Creating TF-IDF features...")
    vectorizer = TfidfVectorizer(stop_words='english', analyzer='word', ngram_range=(1, 2), sublinear_tf=True)
    X_train_vector = vectorizer.fit_transform(X_train)
    X_test_vector = vectorizer.transform(X_test)

    models = {
        "Logistic Regression C=1": LogisticRegression(C=1.0, random_state=42, max_iter=1000),
        "Logistic Regression C=10": LogisticRegression(C=10.0, random_state=42, max_iter=1000),
        "Linear SVC C=1": CalibratedClassifierCV(LinearSVC(C=1.0, random_state=42, dual="auto", max_iter=5000), cv=5),
        "Linear SVC C=50": CalibratedClassifierCV(LinearSVC(C=50.0, random_state=42, dual="auto", max_iter=5000), cv=5),
        "Multinomial Naive Bayes": MultinomialNB(),
        "Complement Naive Bayes": ComplementNB(),
        "SGD Classifier": SGDClassifier(loss='log_loss', random_state=42, max_iter=1000),
        "Random Forest": RandomForestClassifier(n_estimators=200, random_state=42)
    }

    results = []
    trained_models = {}

    print("Training:")
    for idx, (name, model) in enumerate(models.items(), 1):
        print(f"[{idx}] {name}")
        start_time = time.time()
        model.fit(X_train_vector, y_train)
        end_time = time.time()
        
        y_pred = model.predict(X_test_vector)
        
        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred, average='macro', zero_division=0)
        rec = recall_score(y_test, y_pred, average='macro', zero_division=0)
        macro_f1 = f1_score(y_test, y_pred, average='macro', zero_division=0)
        weighted_f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)
        
        train_time = end_time - start_time
        
        results.append({
            "Model": name,
            "Accuracy": acc,
            "Precision": prec,
            "Recall": rec,
            "Macro F1": macro_f1,
            "Weighted F1": weighted_f1,
            "Training Time": train_time
        })
        trained_models[name] = model

    print("\nEvaluating models...")
    results_df = pd.DataFrame(results)
    
    print("\n===========================================")
    print("SUPPORTPILOT MODEL COMPARISON")
    print("Model\t\t\tAccuracy")
    for row in results_df.itertuples():
        print(f"{row.Model:<25} {row.Accuracy*100:.2f}%")
    print("===========================================")
    print("Macro F1:")
    for row in results_df.itertuples():
        print(f"{row.Model:<25} {getattr(row, '_5')*100:.2f}%")
    print("===========================================\n")

    print("Selecting best model...")
    # Selection logic: Highest Macro F1 -> Highest Accuracy -> Highest Weighted F1
    best_row = results_df.sort_values(by=['Macro F1', 'Accuracy', 'Weighted F1'], ascending=[False, False, False]).iloc[0]
    best_model_name = best_row['Model']
    best_model = trained_models[best_model_name]

    print(f"BEST MODEL: {best_model_name}")

    os.makedirs("models", exist_ok=True)
    os.makedirs("evaluation", exist_ok=True)
    
    print("Saving best model...")
    joblib.dump(best_model, "models/ticket_classifier.pkl")
    print("Saving vectorizer...")
    joblib.dump(vectorizer, "models/vectorizer.pkl")
    
    # Save model metadata
    model_metadata = {
        "model_name": best_model_name,
        "accuracy": best_row["Accuracy"],
        "macro_f1": best_row["Macro F1"],
        "weighted_f1": best_row["Weighted F1"],
        "classes": best_model.classes_.tolist()
    }
    with open("models/model_metadata.json", "w") as f:
        json.dump(model_metadata, f, indent=4)
        
    print("Saving evaluation results...")
    results_df.to_csv("evaluation/model_comparison.csv", index=False)
    
    # Best model eval
    y_pred_best = best_model.predict(X_test_vector)
    report = classification_report(y_test, y_pred_best, target_names=best_model.classes_)
    with open("evaluation/classification_report.txt", "w") as f:
        f.write(report)
        
    cm = confusion_matrix(y_test, y_pred_best, labels=best_model.classes_)
    plt.figure(figsize=(10, 7))
    sns.heatmap(cm, annot=True, fmt='d', xticklabels=best_model.classes_, yticklabels=best_model.classes_, cmap='Blues')
    plt.xlabel('Predicted')
    plt.ylabel('Actual')
    plt.title(f'Confusion Matrix - {best_model_name}')
    plt.tight_layout()
    plt.savefig("evaluation/confusion_matrix.png")
    
    print("Training complete.")

if __name__ == "__main__":
    train_and_save_model()