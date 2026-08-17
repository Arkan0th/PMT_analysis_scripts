import os

def rename_files_preserve_ext(directory, base_name):
    files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
    files.sort()

    for idx, filename in enumerate(files, start=1):
        file_ext = os.path.splitext(filename)[1]
        new_name = f"{base_name}---{idx:04d}{file_ext}"
        src = os.path.join(directory, filename)
        dst = os.path.join(directory, new_name)
        os.rename(src, dst)
        print(f"Renamed: {filename} -> {new_name}")

if __name__ == "__main__":
    directory = input("Enter directory path: ").strip()
    base_name = input("Enter base filename: ").strip()
    print("### starting ###")

    if os.path.isdir(directory):
        rename_files_preserve_ext(directory, base_name)
        print("### finished ###")

