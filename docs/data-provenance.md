# Data provenance and import boundaries

## BachataSteps discussion prototype

The command `python manage.py seed_bachata_demo` creates 37 discussion topics and movement records
from a bounded,
manually reviewed metadata sample retrieved on 2026-11-01 from the public BachataSteps catalog
linked in the r/Bachata post below.

Sources:

- Reddit project post: <https://www.reddit.com/r/Bachata/comments/1bneys8/>
- Public catalog: <https://bachatasteps.com/>

Stored fields are limited to a movement name, catalog difficulty, category tags, named
creator/demonstrator, catalog identifier, and outbound source links. VDanceHub does not download,
copy, proxy, or host the catalog's videos, thumbnails, private notes, or user data.

The seed also creates ten normalized concept nodes and proposed, name-derived component edges.
Those inferred relationships are visibly labeled as proposals and require community review.

This 37-record seed is a product and usability prototype, not a claim that the upstream catalog
is openly licensed for bulk republication. Before any broader or recurring import, obtain written
permission or a documented license from the catalog owner, agree on attribution and removal
mechanisms, and replace the research-only extraction with a rate-limited supported export or API.

The seed is idempotent and is never run automatically during deployment. Operators must choose to
run it in the intended environment.

## Three-curriculum knowledge-graph pilot

The command `python manage.py seed_curriculum_pilot` creates three attributed curriculum snapshots,
ten ordered modules, shared concept nodes, three review discussions, and proposed ordering-derived
edges. The bounded source set was manually reviewed on 2026-11-01:

- Rumba y Timbal video library: <https://www.rumbaytimbal.com/rumba-video-library/>
- MIT Casino Rueda syllabus: <https://casinorueda.mit.edu/syllabus/>
- r/Bachata syllabus discussion: <https://www.reddit.com/r/Bachata/comments/1igk3vo/>

The seed stores curriculum and movement titles, concise original summaries, ordering, attribution,
and canonical links. It does not copy lesson descriptions, videos, images, or proprietary course
materials. A module's published ordering supports `TAUGHT_IN` membership; consecutive ordering is
represented only as an imported, proposed prerequisite and is explicitly open to community review.

The seed is idempotent and never runs automatically during deployment.
