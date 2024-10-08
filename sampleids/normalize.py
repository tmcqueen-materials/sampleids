from sampleids.id import SampleID

# tool_id_aliases is a dictionary like {'DINGUS': ['DINGS', 'DINGIS'], ...} where the canonical name is the key and the value is a list of aliases (exact matches)
# provenance_id_aliases is similar
# ids not found are left unchanged
def normalize(sid, tool_id_aliases, provenance_id_aliases):
  tid = sid.tool_id
  if not (tid in tool_id_aliases.keys()):
    for a in tool_id_aliases:
      if tid in tool_id_aliases[a]:
        tid = a
        break
  pid_all = sid.provenance_id
  pid_new = []
  for pid in pid_all:
    if not (pid in provenance_id_aliases.keys()):
      for a in provenance_id_aliases:
        if pid in provenance_id_aliases[a]:
          pid = a
          break
    pid_new.append(pid)
  return SampleID(lab_id=sid.lab_id,tool_id=tid, date=sid.date, sample_id=sid.sample_id, provenance_id=pid_new, split_id=sid.split_id, extra=sid.extra, raw=sid.raw, confidence=sid.confidence, why=sid.why)

