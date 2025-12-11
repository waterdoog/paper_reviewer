import openreview

client = openreview.api.OpenReviewClient(
    baseurl="https://api.openreview.net"
)

notes = client.get_notes(
    forum="7MPstNz66e",
    details="all",
    limit=1000
)

print("✅ total notes:", len(notes))
print("First invitation:", notes[0].invitation)
