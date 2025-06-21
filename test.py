user = ["devlord", "dare", "1234"]
for u in user:
    uuid = u.replace("@","").strip() if u.startswith("@") and not u.isdigit() else u
    print(uuid)