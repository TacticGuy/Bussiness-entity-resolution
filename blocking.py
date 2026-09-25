"""Disk-backed candidate generation for the entity-resolution challenge."""
import argparse
import csv
import os
import sqlite3

from normalize import blocking_keys


def build_index(source_paths, db_path):
	if os.path.exists(db_path):
		os.remove(db_path)
	connection = sqlite3.connect(db_path)
	connection.execute("PRAGMA journal_mode=OFF")
	connection.execute("PRAGMA synchronous=OFF")
	connection.executescript(
		"""
		CREATE TABLE blocks (block_key TEXT NOT NULL, entity_id TEXT NOT NULL);
		"""
	)
	block_rows = []
	for path in source_paths:
		with open(path, encoding="utf-8", newline="") as handle:
			for row in csv.DictReader(handle, delimiter="\t"):
				entity_id = row["entity_id"]
				block_rows.extend((key, entity_id) for key in blocking_keys(
					row.get("business_name", ""), row.get("business_address", "")))
				if len(block_rows) >= 10000:
					connection.executemany("INSERT INTO blocks VALUES (?, ?)", block_rows)
					connection.commit()
					block_rows.clear()
	if block_rows:
		connection.executemany("INSERT INTO blocks VALUES (?, ?)", block_rows)
	connection.execute("CREATE INDEX blocks_key ON blocks(block_key)")
	connection.commit()
	return connection


def write_candidates(source1_path, connection, output_path, max_candidates=5000):
	with open(source1_path, encoding="utf-8", newline="") as source1, \
			open(output_path, "w", encoding="utf-8", newline="") as output:
		writer = csv.writer(output, delimiter="\t", lineterminator="\n")
		writer.writerow(["source1_entity_id", "candidate_entity_ids"])
		for row in csv.DictReader(source1, delimiter="\t"):
			keys = list(blocking_keys(row.get("business_name", ""), row.get("business_address", "")))
			candidates = set()
			for key in keys:
				candidates.update(candidate[0] for candidate in connection.execute(
					"SELECT entity_id FROM blocks WHERE block_key = ? LIMIT ?", (key, max_candidates)))
			writer.writerow([row["entity_id"], ",".join(sorted(candidates))])


def main():
	parser = argparse.ArgumentParser(description="Build candidate-pair TSVs.")
	parser.add_argument("--source1", required=True)
	parser.add_argument("--source2", required=True)
	parser.add_argument("--source3", required=True)
	parser.add_argument("--out", required=True)
	parser.add_argument("--index", required=True)
	parser.add_argument("--max-candidates", type=int, default=5000)
	args = parser.parse_args()
	os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
	connection = build_index([args.source2, args.source3], args.index)
	try:
		write_candidates(args.source1, connection, args.out, args.max_candidates)
	finally:
		connection.close()
	print(f"Wrote candidates to {args.out}")


if __name__ == "__main__":
	main()
