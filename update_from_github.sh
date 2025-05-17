#!/bin/bash
# Script to update from JCA374/ReplitStock while preserving secrets and config

REPO_URL="https://github.com/JCA374/ReplitStock.git"
REPO_NAME="ReplitStock"

# Function to backup important files
backup_important_files() {
    # Create backup directory if it doesn't exist
    mkdir -p ./backup
    
    # Backup secrets.toml if it exists
    if [ -f .streamlit/secrets.toml ]; then
        cp .streamlit/secrets.toml ./backup/secrets.toml.bak
        echo "✅ Backed up secrets.toml"
    fi
    
    # Backup config.toml if it exists
    if [ -f .streamlit/config.toml ]; then
        cp .streamlit/config.toml ./backup/config.toml.bak
        echo "✅ Backed up config.toml"
    fi
}

# Function to restore important files
restore_important_files() {
    # Restore secrets.toml if backup exists
    if [ -f ./backup/secrets.toml.bak ]; then
        mkdir -p .streamlit
        cp ./backup/secrets.toml.bak .streamlit/secrets.toml
        echo "✅ Restored secrets.toml"
    fi
}

# Function to update config.toml
update_config_toml() {
    mkdir -p .streamlit
    
    if [ -f .streamlit/config.toml ]; then
        # Check if address line exists
        if grep -q "address" .streamlit/config.toml; then
            # Update existing address line
            sed -i 's/address = "0.0.0.0"/address = "localhost"/' .streamlit/config.toml
            sed -i 's/address = "127.0.0.1"/address = "localhost"/' .streamlit/config.toml
        else
            # Add address line if not present
            echo 'address = "localhost"' >> .streamlit/config.toml
        fi
    else
        # Create minimal config file
        echo '[server]' > .streamlit/config.toml
        echo 'address = "localhost"' >> .streamlit/config.toml
        echo 'port = 5000' >> .streamlit/config.toml
    fi
    
    echo "✅ Updated config.toml to use localhost"
}

echo "🔄 Updating from $REPO_URL"

# Check if we're in a git repository
if [ -d .git ]; then
    echo "Git repository found, performing update..."
    
    # Backup important files
    backup_important_files
    
    # Check the remote origin URL
    CURRENT_REMOTE=$(git remote get-url origin 2>/dev/null)
    
    # If origin is not set to the right repo, set it
    if [ "$CURRENT_REMOTE" != "$REPO_URL" ]; then
        echo "Setting remote origin to $REPO_URL"
        git remote set-url origin $REPO_URL 2>/dev/null || git remote add origin $REPO_URL
    fi
    
    # Stash your secrets file
    if [ -f .streamlit/secrets.toml ]; then
        git stash push .streamlit/secrets.toml
        echo "✅ Stashed secrets.toml"
    fi
    
    # Pull the latest changes
    echo "Pulling latest changes..."
    git pull origin main
    
    # Apply your stashed secrets file
    if [ -f .streamlit/secrets.toml ]; then
        git stash pop
        echo "✅ Restored secrets.toml from stash"
    else
        restore_important_files
    fi
    
    # Update config.toml to use localhost
    update_config_toml
    
else
    echo "Git repository not found. Cloning from $REPO_URL..."
    
    # Check if we're in the repo directory already
    if [ "$(basename $(pwd))" == "$REPO_NAME" ]; then
        # We're in a directory with the same name but not initialized
        # Backup important files
        backup_important_files
        
        # Initialize git and set remote
        git init
        git remote add origin $REPO_URL
        
        # Fetch the code
        git fetch
        
        # Create .gitignore to protect secrets
        echo ".streamlit/secrets.toml" > .gitignore
        
        # Reset to the fetched state
        git reset --hard origin/main
        
        # Restore important files
        restore_important_files
        
        # Update config.toml
        update_config_toml
        
    else
        # We need to clone to a new directory
        echo "Cloning to ./$REPO_NAME directory..."
        git clone $REPO_URL
        
        echo "Please move your secrets.toml to $REPO_NAME/.streamlit/ after this script finishes"
        echo "Then run this script again from inside the $REPO_NAME directory to update config.toml"
        
        echo "✅ Repository cloned successfully to $REPO_NAME"
        echo "⚠️ Don't forget to set up your secrets.toml file in $REPO_NAME/.streamlit/"
    fi
fi

echo ""
echo "🎉 Done! You can now run the app with: streamlit run app.py"
echo "   Access the app at: http://localhost:5000"