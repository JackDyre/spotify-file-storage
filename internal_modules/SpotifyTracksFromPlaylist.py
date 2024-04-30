from internal_modules.SpotipyAPIClient import initialize_api
import tkinter as tk

sp = initialize_api()

def input_url() -> str:

    url = ''

    def get_url_from_entry(*args):
        nonlocal url
        url = url_var.get()
        root.destroy()

    width: int = 550
    height: int = 200

    root = tk.Tk()

    root.title('Input Spotify playlist URL')

    left = (root.winfo_screenwidth() - width)//2
    top = (root.winfo_screenheight() - height)//2
    root.geometry(f'{width}x{height}+{left}+{top}')

    root.bind('<Return>', get_url_from_entry)
    frame: tk.Frame = tk.Frame(root)
    frame.pack(expand=True)
    root.after(ms=1, func=root.focus_force)

    tk.Label(frame, text='Input Spotify playlist URL:').pack(pady=5)

    url_var = tk.StringVar(frame, name='answer')
    entry_box: tk.Entry = tk.Entry(frame, textvariable=url_var, width=75)
    entry_box.pack(pady=5)
    entry_box.focus_set()

    tk.Button(frame, text='Enter', command=get_url_from_entry).pack(pady=5)

    root.mainloop()

    if not 'https://open.spotify.com/playlist/' in url:
        print('Please input a valid Spotify playlist URL')
        url = input_url()

    return url
    


def get_tracks(url: str | None=None, market: str = 'US') -> tuple[list, int, bool]:

    playlist_url: str = url or input_url()
    is_error: bool = False
    tracks: list = []; offset = 0


    try:
        
        width: int = 275
        height: int = 100

        root = tk.Tk()
        root.title('Fetching Tracks')

        left = (root.winfo_screenwidth() - width)//2
        top = (root.winfo_screenheight() - height)//2
        root.geometry(f'{width}x{height}+{left}+{top}')


        frame: tk.Frame = tk.Frame(root)
        frame.pack(expand=True)
        root.after(ms=1, func=root.focus_force)

        progress_var = tk.StringVar(frame, name='Progress')
        label = tk.Label(frame, textvariable=progress_var)
        label.pack(pady=5)

        total_tracks: int = sp.playlist(playlist_url)["tracks"]["total"]
    
        while True:
            track_batch = sp.playlist_tracks(playlist_url, offset=offset, market=market)
            offset += 100
            for track in track_batch["items"]:
                tracks.append(track["track"])

            progress = 100 * len(tracks) / (total_tracks or 1)
            progress_var.set(f"Fetching Tracks: {progress:.2f}%")
            root.update()
            if not track_batch["next"]:
                root.destroy()
                break
    
    except Exception as e:
        total_tracks = 0
        print(f'An API error was encountered. Please try again\n{e}')
        is_error = True
        root.destroy()

    return (tracks, total_tracks, is_error)
