# Spotify File Storage


## Introduction

A python project that *~~steals~~* borrows file storage from Spotify for free and create virtual file systems in the form of Spotify playlists.

## Usage

### Spotify API Credentials

To use this project you must provide your own API keys that are associated with your Spotify account. Read [this](https://developer.spotify.com/documentation/web-api/concepts/apps) to learn about setting up your Spotify Web API app and you will be able to find the `client_id` and `client_secret` in your Spotify developer dashboard. You will be prompted to input your credentials the first time you run this project.

### File Environments

This project stores your files in a password protected 'file environment'. When you run `main.py` you will be prompted to input a file environment password. It will search your library for a match and will load the matching file environment if found. If no match is found in your library, you will be prompted again to input the password of the file environment to be created.

**Warning:** There is no recovery process for file environment passwords. You are responsible for keeping track of them. If you lose the environment password, you will no longer be able to remove any playlists from that file environment since all playlists are meant to appear the same.

### File Privacy

Your files stored on spotify are fairly secure, especially if you fetch your own set of track IDs to be referenced rather than the defaults that I fetched. Instructions on configuring your own set of IDs will be written shortly.

## Dependencies

Requires [spotipy](https://pypi.org/project/spotipy/)

```
pip install spotipy
```
