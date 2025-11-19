import requests
import os
from pathlib import Path

# Create directory for audio files
audio_dir = Path("english_conversations")
audio_dir.mkdir(exist_ok=True)

# List of free English conversation audio URLs from Internet Archive
audio_files = {
    "English_Conversation_Practice.mp3": "https://archive.org/download/englishaudio/1-English%20Conversation%20Listening%20Practice%20English%20Practice%20Listening%20to%20Naturally.mp3",
    "Easy_English_Conversations_02.mp3": "https://archive.org/download/englishaudio/10-%20Learn%20English%20Speaking%20Easy%20English%20Conversations%2002.mp3",
    "Easy_English_Conversations_03.mp3": "https://archive.org/download/englishaudio/11%20-%20Learn%20English%20Speaking%20Easy%20English%20Conversations%2003.mp3",
    "Easy_English_Conversations_04.mp3": "https://archive.org/download/englishaudio/12%20-%20Learn%20English%20Speaking%20Easy%20English%20Conversations%2004.mp3",
    "American_English_Conversations.mp3": "https://archive.org/download/englishaudio/2%20-%20American%20English%20Conversations%20to%20Improve%20Listening%20Speaking%20Fluency%20English%20Conversation.mp3",
    "Two_Friends_Conversation.mp3": "https://archive.org/download/englishaudio/3-%20Conversation%20Between%20Two%20Friends%20In%20English%20Speaking%20Short%20Dialogues%20In%20English%20With%20Subtitles.mp3",
    "English_For_Traveling.mp3": "https://archive.org/download/englishaudio/4%20-%20Practice%20English%20Speaking%20Everyday%20with%20Subtitles%20English%20Conversation%20for%20Traveling%20Holiday.mp3",
    "75_Daily_Conversations.mp3": "https://archive.org/download/englishaudio/6%20-%2075%20Daily%20English%20Conversations%20Practice%20Learn%20English%20Speaking%20Practice.mp3",
}

def download_file(url, filename):
    """Download a file with progress indication"""
    try:
        print(f"\n📥 Downloading: {filename}")
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        
        file_path = audio_dir / filename
        
        with open(file_path, 'wb') as f:
            if total_size == 0:
                f.write(response.content)
            else:
                downloaded = 0
                chunk_size = 8192
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        percent = (downloaded / total_size) * 100
                        print(f"  Progress: {percent:.1f}% ({downloaded / 1024 / 1024:.1f} MB)", end='\r')
        
        file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
        print(f"\n  ✅ Downloaded: {filename} ({file_size:.1f} MB)")
        return True
        
    except Exception as e:
        print(f"\n  ❌ Error downloading {filename}: {e}")
        return False

def main():
    print("=" * 60)
    print("English Conversation Audio Downloader")
    print("=" * 60)
    print(f"\nDownloading to: {audio_dir.absolute()}")
    print(f"Number of files: {len(audio_files)}")
    
    # Ask user which files to download
    print("\n" + "=" * 60)
    choice = input("Download all files? (y/n) or enter number of files to download: ").strip().lower()
    
    files_to_download = list(audio_files.items())
    
    if choice == 'n':
        print("\nAvailable files:")
        for idx, (filename, _) in enumerate(files_to_download, 1):
            print(f"  [{idx}] {filename}")
        
        selections = input("\nEnter file numbers to download (comma-separated, e.g., 1,2,3): ").strip()
        try:
            indices = [int(x.strip()) - 1 for x in selections.split(',')]
            files_to_download = [files_to_download[i] for i in indices if 0 <= i < len(files_to_download)]
        except:
            print("Invalid selection. Downloading first 3 files.")
            files_to_download = files_to_download[:3]
    
    elif choice.isdigit():
        num = int(choice)
        files_to_download = files_to_download[:num]
    
    # Download files
    print("\n" + "=" * 60)
    print(f"Downloading {len(files_to_download)} file(s)...")
    print("=" * 60)
    
    successful = 0
    failed = 0
    
    for filename, url in files_to_download:
        if download_file(url, filename):
            successful += 1
        else:
            failed += 1
    
    # Summary
    print("\n" + "=" * 60)
    print("Download Summary")
    print("=" * 60)
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"📁 Files saved to: {audio_dir.absolute()}")
    
    # List downloaded files
    downloaded_files = list(audio_dir.glob("*.mp3"))
    if downloaded_files:
        print(f"\n📋 Downloaded files:")
        for f in downloaded_files:
            size = os.path.getsize(f) / (1024 * 1024)
            print(f"  • {f.name} ({size:.1f} MB)")


main()