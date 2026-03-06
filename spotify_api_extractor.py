#!/usr/bin/env python3
"""
PowerUp Spotify Liked Songs Extractor - Official API Version
This script uses the official Spotify Web API to extract ALL liked songs reliably.
"""

import spotipy
from spotipy.oauth2 import SpotifyOAuth
import csv
import os
import sys
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SpotifyAPIExtractor:
    def __init__(self):
        """Initialize the Spotify API extractor"""
        self.client_id = None  # Will be prompted
        self.client_secret = None  # Will be prompted
        self.redirect_uri = "http://127.0.0.1:8080/callback"
        self.scope = "user-library-read"
        self.sp = None
        self.songs = []
        
    def setup_credentials(self):
        """Set up Spotify API credentials"""
        logger.info("🔐 Setting up Spotify API credentials...")
        
        print("\n🎵 PowerUp Spotify API Extractor")
        print("=" * 50)
        print("To use the Spotify API, you need to create a Spotify App.")
        print("Don't worry - this is free and takes 2 minutes!")
        print()
        
        # Check if we already have credentials
        if os.path.exists('.env'):
            logger.info("Found existing .env file")
            try:
                with open('.env', 'r') as f:
                    for line in f:
                        if line.startswith('SPOTIPY_CLIENT_ID='):
                            self.client_id = line.split('=', 1)[1].strip()
                        elif line.startswith('SPOTIPY_CLIENT_SECRET='):
                            self.client_secret = line.split('=', 1)[1].strip()

                if self.client_id and self.client_secret:
                    logger.info("✅ Using existing credentials")
                    return True
            except Exception as e:
                logger.warning(f"Error reading .env file: {e}")
        
        # Guide user through setup
        print("📋 SETUP INSTRUCTIONS:")
        print("1. Go to: https://developer.spotify.com/dashboard")
        print("2. Log in with your Spotify account")
        print("3. Click 'Create App'")
        print("4. Fill in:")
        print("   - App Name: PowerUp Spotify Extractor")
        print("   - App Description: Extract my liked songs")
        print("   - Website: https://localhost:8888/")
        print("   - Redirect URI: http://127.0.0.1:8080/callback")
        print("5. Check 'Web API' and agree to terms")
        print("6. Click 'Save'")
        print("7. Click 'Settings' on your new app")
        print("8. Copy the 'Client ID' and 'Client Secret'")
        print()

        # Get client ID from user
        while not self.client_id:
            self.client_id = input("📝 Paste your Client ID here: ").strip()
            if not self.client_id:
                print("❌ Client ID cannot be empty. Please try again.")

        # Get client secret from user
        while not self.client_secret:
            self.client_secret = input("📝 Paste your Client Secret here: ").strip()
            if not self.client_secret:
                print("❌ Client Secret cannot be empty. Please try again.")
        
        # Save credentials
        try:
            with open('.env', 'w') as f:
                f.write(f"SPOTIPY_CLIENT_ID={self.client_id}\n")
                f.write(f"SPOTIPY_CLIENT_SECRET={self.client_secret}\n")
                f.write(f"SPOTIPY_REDIRECT_URI={self.redirect_uri}\n")
            
            logger.info("✅ Credentials saved to .env file")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error saving credentials: {e}")
            return False
    
    def authenticate(self):
        """Authenticate with Spotify API"""
        logger.info("🔑 Authenticating with Spotify...")
        
        try:
            # Set up OAuth
            auth_manager = SpotifyOAuth(
                client_id=self.client_id,
                client_secret=self.client_secret,
                redirect_uri=self.redirect_uri,
                scope=self.scope,
                cache_path=".spotify_cache"
            )
            
            # Create Spotify client
            self.sp = spotipy.Spotify(auth_manager=auth_manager)
            
            # Test authentication
            user = self.sp.current_user()
            logger.info(f"✅ Successfully authenticated as: {user['display_name']} ({user['id']})")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Authentication failed: {e}")
            logger.error("💡 Make sure your Client Secret is correct and try again")
            return False
    
    def extract_liked_songs(self):
        """Extract all liked songs using pagination"""
        logger.info("🎵 Extracting all liked songs...")
        
        try:
            songs = []
            offset = 0
            limit = 50  # Maximum allowed by Spotify API
            
            while True:
                logger.info(f"📥 Fetching songs {offset + 1}-{offset + limit}...")
                
                # Get batch of liked songs
                results = self.sp.current_user_saved_tracks(limit=limit, offset=offset)
                
                if not results['items']:
                    break
                
                # Process each song
                for item in results['items']:
                    track = item['track']
                    
                    # Extract song information
                    song = {
                        'title': track['name'],
                        'artist': ', '.join([artist['name'] for artist in track['artists']]),
                        'album': track['album']['name'],
                        'added_at': item['added_at'],
                        'spotify_id': track['id'],
                        'spotify_url': track['external_urls']['spotify']
                    }
                    
                    songs.append(song)
                
                # Check if we have more songs
                if len(results['items']) < limit:
                    break
                
                offset += limit
                
                # Progress update
                if len(songs) % 50 == 0:
                    logger.info(f"🎉 Found {len(songs)} songs so far...")
            
            self.songs = songs
            logger.info(f"🎉 Successfully extracted {len(songs)} liked songs!")
            
            # Show preview
            if songs:
                logger.info("📋 Preview of extracted songs:")
                for i, song in enumerate(songs[:5]):
                    logger.info(f"  {i+1}. \"{song['title']}\" by {song['artist']} ({song['album']})")
                
                if len(songs) > 5:
                    logger.info(f"... and {len(songs) - 5} more songs")
            
            return songs
            
        except Exception as e:
            logger.error(f"❌ Error extracting songs: {e}")
            return []
    
    def save_to_csv(self, filename="spotify_liked_songs_api.csv"):
        """Save extracted songs to CSV file"""
        if not self.songs:
            logger.error("❌ No songs to save!")
            return False
        
        logger.info(f"💾 Saving {len(self.songs)} songs to {filename}...")
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                # Use same format as previous attempts for consistency
                fieldnames = ['title', 'artist', 'album']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for song in self.songs:
                    # Only include the basic fields for consistency
                    row = {
                        'title': song['title'],
                        'artist': song['artist'],
                        'album': song['album']
                    }
                    writer.writerow(row)
            
            full_path = os.path.abspath(filename)
            logger.info(f"✅ CSV file saved: {full_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error saving CSV: {e}")
            return False
    
    def save_detailed_csv(self, filename="spotify_liked_songs_detailed.csv"):
        """Save extracted songs with all details to CSV file"""
        if not self.songs:
            logger.error("❌ No songs to save!")
            return False
        
        logger.info(f"💾 Saving detailed data to {filename}...")
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile: 
                fieldnames = ['title', 'artist', 'album', 'added_at', 'spotify_id', 'spotify_url']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for song in self.songs:
                    writer.writerow(song)
            
            full_path = os.path.abspath(filename)
            logger.info(f"✅ Detailed CSV file saved: {full_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error saving detailed CSV: {e}")
            return False
    
    def run(self):
        """Main extraction process"""
        logger.info("🎵 PowerUp Spotify API Extractor")
        logger.info("=" * 50)
        
        # Setup credentials
        if not self.setup_credentials():
            return False
        
        # Authenticate
        if not self.authenticate():
            return False
        
        # Extract songs
        songs = self.extract_liked_songs()
        
        if not songs:
            logger.error("❌ No songs extracted!")
            return False
        
        # Save to CSV files
        basic_saved = self.save_to_csv()
        detailed_saved = self.save_detailed_csv()
        
        if basic_saved:
            logger.info("🎉 Extraction complete!")
            logger.info(f"📁 Basic CSV: spotify_liked_songs_api.csv")
            if detailed_saved:
                logger.info(f"📁 Detailed CSV: spotify_liked_songs_detailed.csv")
            
            logger.info(f"🎵 Total songs extracted: {len(songs)}")
            return True
        else:
            logger.error("❌ Failed to save songs!")
            return False

def main():
    """Main function"""
    print("🎵 PowerUp Spotify Liked Songs Extractor - API Version")
    print("=" * 60)
    print("This tool uses the official Spotify Web API to extract ALL your liked songs.")
    print("It's 100% reliable and will get every single song!")
    print()
    
    extractor = SpotifyAPIExtractor()
    success = extractor.run()
    
    if success:
        print("\n🎉 SUCCESS! All your liked songs have been extracted!")
        print("📁 Check the CSV files in this directory.")
        print("💡 The basic CSV matches the format from previous attempts.")
        print("💡 The detailed CSV includes additional metadata.")
    else:
        print("\n❌ Extraction failed. Please check the logs above.")

if __name__ == "__main__":
    main()
