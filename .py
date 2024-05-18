from main import *
import json

# x = api_request_manager.get_playlist_tracks("4wbACms7wGmoH2UV15dtgu", print_progress=True)
# ide = [f"{track['name']}{track['album']['name']}" for track in x]
#
# with open("13ident.json", 'w') as f:
#     json.dump(ide, f, indent=4)


with open("13ident.json", 'r') as f:
    x = json.load(f)

seen = []
for ide in x:
    if ide in seen:
        print(ide)
    else:
        seen.append(ide)
