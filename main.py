import subprocess
import os
import sys

def run_command(command):
    """
    Executes a shell command and returns the output, or None on error.
    Prints both stdout and stderr in real-time.
    """
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

    while True:
        output = process.stdout.readline()
        if output:
            print(output.strip())  # Print stdout in real-time

        error = process.stderr.readline()
        if error:
            print(error.strip(), file=sys.stderr) # Print stderr in real-time

        return_code = process.poll()
        if return_code is not None:
            # Ensure all remaining output is read after the process finishes.
            for output in process.stdout:
                print(output.strip())
            for error in process.stderr:
                print(error.strip(), file=sys.stderr)
            if return_code == 0:
                return True # Indicate success
            else:
                print(f"Command failed with exit code {return_code}")
                return False # Indicate failure
            break

def check_root():
    """
    Checks if the script is running with root privileges using os.geteuid().
    Returns True if the user is root, False otherwise.
    """
    return os.geteuid() == 0

def create_user(username, password):
    """
    Creates a new user account with the given username and password.
    Uses subprocess.run() for security and handles potential errors.
    """
    if not check_root():
        print("Error: This operation requires root privileges.")
        return False

    # Use 'useradd' to create the user, and handle errors.
    useradd_command = f"useradd -m {username}" # -m creates home directory
    if not run_command(useradd_command):
        print(f"Failed to create user {username}")
        return False

    # Use 'passwd' in a non-interactive way to set the password
    passwd_command = f"echo "{username}:{password}" | chpasswd"
    if not run_command(passwd_command):
        print(f"Failed to set password for user {username}.")
        # Attempt to delete the user we created, to rollback.
        del_user_command = f"userdel -r {username}"
        run_command(del_user_command) # Don't check result, just try to clean up.
        return False

    print(f"User account '{username}' created successfully.")
    return True

def add_user_to_group(username, groupname):
    """Adds a user to a group."""
    if not check_root():
        print("Error: This operation requires root privileges.")
        return False

    usermod_command = f"usermod -a -G {groupname} {username}"
    if not run_command(usermod_command):
        print(f"Failed to add user {username} to group {groupname}")
        return False
    print(f"User {username} added to group {groupname}")
    return True

def enable_auto_login(username):
    """
    Enables automatic login for the specified user by modifying system configuration.
    This function modifies /etc/lightdm/lightdm.conf (for LightDM).  This is highly DESTRUCTIVE.
    It's safer to provide instructions, not a script, but I've added a check.
    """
    if not check_root():
        print("Error: This operation requires root privileges.")
        return False

    # Check if the lightdm.conf file exists.
    if not os.path.exists("/etc/lightdm/lightdm.conf"):
        print("/etc/lightdm/lightdm.conf does not exist.  Auto-login setup is not supported on this system, or LightDM is not the display manager.")
        return False

    # This is inherently dangerous, as it modifies a system file.
    #  We will make a backup.
    backup_command = "cp /etc/lightdm/lightdm.conf /etc/lightdm/lightdm.conf.bak"
    if not run_command(backup_command):
        print("Failed to backup /etc/lightdm/lightdm.conf.  Aborting auto-login configuration.")
        return False

    # Use sed to modify the file.
    sed_command = (
        f"sed -i 's/^#automatic_login_enable = false/automatic_login_enable = true/g; "
        f"s/^#automatic_login_user =$/automatic_login_user = {username}/g' /etc/lightdm/lightdm.conf"
    )
    if not run_command(sed_command):
        print("Failed to modify /etc/lightdm/lightdm.conf.  Auto-login may not be configured correctly.")
        return False  # Do NOT return True if sed fails.

    print(f"Automatic login enabled for user '{username}'.  Please reboot the system.")
    return True # Return True only if the sed command *succeeds*.

def list_users():
    """
    Lists the users on the system.
    """
    if not check_root():
        print("Error: This operation requires root privileges.")
        return False
    
    # getent passwd returns all user accounts
    getent_command = "getent passwd | cut -d: -f1"
    process = subprocess.Popen(getent_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    output, error = process.communicate() # Get all output at once.
    
    if process.returncode != 0:
        print(f"Error listing users: {error}")
        return False

    users = output.strip().split('\n')
    if not users:
        print("No users found on the system.")
        return True

    print("Users on the system:")
    for user in users:
        print(user)
    return True

def main():
    """
    Main function to provide a user-friendly menu for login and user management.
    """
    if not check_root():
        print("Warning: This script requires root privileges for most operations.  Some options will be unavailable.")

    while True:
        print("\nLinux Login and User Management Menu")
        print("1. Create User")
        print("2. Enable Auto-Login")
        print("3. List Users")
        print("4. Add user to group")
        print("5. Exit")

        choice = input("Enter your choice: ")

        if choice == '1':
            username = input("Enter the username for the new account: ")
            password = input("Enter the password for the new account: ")
            if create_user(username, password):
                print("User created successfully.")
            else:
                print("User creation failed.")
        elif choice == '2':
            username = input("Enter the username for auto-login: ")
            if enable_auto_login(username):
                print("Auto-login configured.  Reboot required.")
            else:
                print("Auto-login configuration failed.")
        elif choice == '3':
            list_users()
        elif choice == '4':
            username = input("Enter the username to add to a group: ")
            groupname = input("Enter the group name: ")
            add_user_to_group(username, groupname)
        elif choice == '5':
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
