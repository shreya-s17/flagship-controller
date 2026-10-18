"""Current independent-review entrypoint; explicitly rejects author reviews.

Legacy validators and recorded source hashes remain unchanged. Self-reported
independence still cannot be certified by software.
"""
import argparse
import json
from pathlib import Path
from . import review_assessment as legacy
from .review_pack import DIMENSIONS


def validate(pack, submission, dimensions=DIMENSIONS):
    if submission.get('review_role') not in (None, 'independent'):
        raise ValueError('Author/owner/automated review cannot count as independent review')
    return legacy.validate(pack, submission, dimensions)


def assess(pack, submissions, dimensions=DIMENSIONS):
    for submission in submissions:
        validate(pack, submission, dimensions)
    return legacy.assess(pack, submissions, dimensions)


def main():
    p = argparse.ArgumentParser();p.add_argument('--pack', type=Path, required=True)
    p.add_argument('--reviews', type=Path, nargs=2, required=True);p.add_argument('--native', action='store_true')
    args = p.parse_args()
    from .native_review_pack import NATIVE_DIMENSIONS
    print(json.dumps(assess(args.pack, [json.loads(f.read_text()) for f in args.reviews], NATIVE_DIMENSIONS if args.native else DIMENSIONS), indent=2))


if __name__ == '__main__':main()
