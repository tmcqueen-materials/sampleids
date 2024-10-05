from sampleids.id import SampleID, CONFIDENCE
from datetime import datetime
import re

def fix_date(date, file_props):
  # TODO: use file date as an additional constraint
  if (len(date) != 6 and len(date) != 8) or not date.isdigit():
    return date
  if len(date) == 8:
    year = date[0:4]
    month = date[4:6]
    day = date[6:8]
    if int(month) > 12:
      t = month
      month = day
      day = t
    cyear = datetime.now().year
    if (int(year) < 1970 or int(year) > cyear+1 or int(month) > 12) and int(date[4:8]) >= 1970 and int(date[4:8]) <= cyear+1:
      # A MMDDYYYY or DDMMYYYY case
      year = date[4:8]
      month = date[0:2]
      day = date[2:4]
      if int(month) > 12:
        t = month
        month = day
        day = t
  else:
    year = "20" + date[0:2]
    month = date[2:4]
    day = date[4:6]
    if int(month) > 12:
      t = month
      month = day
      day = t
  return "".join([year,month,day])

def is_date(d, file_props):
  if (len(d) != 6 and len(d) != 8) or not d.isdigit():
    return False
  try:
    date = fix_date(d, file_props)
    cyear = datetime.now().year
    # TODO: one could refine this check, by making sure the day is in a valid range given the month and year, but probably not worth the complexity
    if int(date[0:4]) >= 1970 and int(date[0:4]) <= cyear+1 and int(date[4:6]) >= 1 and int(date[4:6]) <= 12 and int(date[6:8]) >= 1 and int(date[6:8]) <= 31:
      return True
    return False
  except:
    return False

def fix_lab_id(d):
  return d.strip().upper()

def is_lab_id(d, lab_ids):
  try:
    if fix_lab_id(d) in lab_ids:
      return True
  except:
    return False
  return False

def fix_tool_id(d):
  return d.strip().upper()

def is_tool_id(d, tool_ids):
  try:
    if fix_tool_id(d) in tool_ids:
      return True
  except:
    return False
  return False

def fix_alphanum(d):
  return d.strip().upper()

def is_alphanum(d):
  try:
    dn = fix_alphanum(d)
    if len(dn) > 2 and dn[0:2] == 'ND': # "Non-destructive" prefix
      dn = dn[2:]
    if len(dn) > 2 or not dn.isalnum(): # we don't have more than 1295 (2 digits base 36) splits/samples per other unique constraints
      return False
    return True
  except:
    return False
  return False

def fix_provenance_id(d):
  #
  # We handle two special cases of provenance. The first is multi-provenance, separated by '+', e.g. TMM+NN+LAP.
  # The second is for each provenance, it can be prefixed with pXXX, where XXX is any non '+' character, giving
  # info on lab book and page. For example, 'p2B104' for 2nd book, page 104.
  #
  ps = d.strip().split('+')
  ops = []
  for p in ps:
    ds = p.split('p')
    if len(ds[0]) > 0:
      ops.append(ds[0].strip().upper())
    else:
      ops.append(p.strip().upper())
  return ops

def is_provenance_id(d, prov_ids):
  try:
    for p in fix_provenance_id(d):
      if not p in prov_ids:
        return False
    return True
  except:
    return False
  return False

def is_num_prov_id(d):
  try:
    if fix_provenance_id(d)[0].isdigit() and int(fix_provenance_id(d)[0]) >= 100 and int(fix_provenance_id(d)[0]) < 999999:
      return True
  except:
    return False
  return False

def parse_internal(fragment, lab_ids, tool_ids, prov_ids, why='', file_props=None, short=False):
  rn1 = fragment.split('_')
  extra = ''
  # _V1 should be incremented each time a change to the below is made that changes the interpretation of a "why" string
  if len(why) > 0:
    why += '_PI_V1'
  else:
    why = 'PI_V1'
  #
  # We create a matrix of which entries could possibly be which values, viz:
  #           Frag 0  Frag 1  Frag 2  Frag 3  Frag 4 ...
  # Lab ID    Yes     No      No      No      No     ...
  # Tool ID   No      Yes     No      No      No     ...
  # Date      No      No      Yes     No      No     ...
  # Number    No      No      No      Yes     No     ...
  # Prov. ID  No      No      No      No      Yes    ...
  #
  # And then use this to decide on the most appropriate interpretation of the fragments. This allows us to accommodate
  # transpositions and similar, while still falling back to the "default" order if we don't recognize pieces.
  #
  # Lab IDs are few and rarely changing, so we recognize as "not in our format" anything without a lab ID
  #
  p_lab_id = []
  p_tool_id = []
  p_date = []
  p_alphanum = []
  p_prov_id = []
  p_num_prov_id = []
  for i in range(0,min(len(rn1),6)):
    n = rn1[i]
    if is_lab_id(n, lab_ids):
      p_lab_id.append(i)
    if is_tool_id(n, tool_ids):
      p_tool_id.append(i)
    if is_date(n, file_props):
      p_date.append(i)
    if is_alphanum(n) and (i > 0 or not is_lab_id(n, lab_ids)):
      p_alphanum.append(i)
    if is_provenance_id(n, prov_ids):
      p_prov_id.append(i)
    elif is_num_prov_id(n): # needs to be elif so it only shows up in one of two prov lists
      p_num_prov_id.append(i)

  if fix_lab_id(rn1[0]) == 'EXT':
    why += '_EXT'
    # Special case external users
    if len(rn1) >= 2:
      why += '2'
      return SampleID(lab_id='EXT', provenance_id=fix_provenance_id(rn1[1]), extra='_'.join(rn1[2:]), raw=fragment, confidence=CONFIDENCE.HIGH, why=why)
    why += '_DEFAULT'
    return SampleID(lab_id='EXT', raw=fragment, confidence=CONFIDENCE.LOW, why=why)
  if fix_lab_id(rn1[0]) == 'PDC':
    why += '_PDC'
    # Allow new numeric IDs for PDC
    p_prov_id = p_prov_id + p_num_prov_id

  if len(p_lab_id) == 0 and not short:
    why += '_NOLABID'
    # cannot process without a candidate lab ID unless we are short form
    return SampleID(raw=fragment, confidence=CONFIDENCE.NONE, why=why)

  if len(rn1) > 6:
    why += '_LONG'
    # Assume _ was used instead of - to separate extra information, and that it is form of length 5 unless 6th position processes as only alphanum, in which case treat it as length 6
    if not (5 in p_lab_id) and not (5 in p_tool_id) and not (5 in p_date) and not (5 in p_prov_id) and (5 in p_alphanum) and len(p_alphanum) > 1:
      why += '1'
      extra = '_'.join(rn1[6:])
      rn1 = rn1[0:6]
    else:
      why += '2'
      if 5 in p_lab_id:
        p_lab_id.remove(5)
      if 5 in p_tool_id:
        p_tool_id.remove(5)
      if 5 in p_date:
        p_date.remove(5)
      if 5 in p_prov_id:
        p_prov_id.remove(5)
      if 5 in p_alphanum:
        p_alphanum.remove(5)
      extra = '_'.join(rn1[5:])
      rn1 = rn1[0:5]

  if (len(rn1) == 2 or len(rn1) > 5) and short: # Sometimes people chain BBB_YYYYMMDD_BBB_YYYYMMDD_... together ad infinitum (even though it is not needed). Handle that by looking at the first ancestor only
    why += '_2S'
    # Expected short form: BBB_YYYYMMDD
    if 0 in p_tool_id and 1 in p_date:
      why += '1'
      return SampleID(lab_id=short.lab_id, tool_id=fix_tool_id(rn1[0]), date=fix_date(rn1[1], file_props), sample_id=short.sample_id, provenance_id=short.provenance_id, extra=extra, raw=fragment, confidence=CONFIDENCE.HIGH, why=why)
    if len(p_tool_id) == 1 and len(p_date) == 1 and len(set(p_tool_id+p_date)) == 2:
      why += '2'
      return SampleID(lab_id=short.lab_id, tool_id=fix_tool_id(rn1[p_tool_id[0]]), date=fix_date(rn1[p_date[0]], file_props), sample_id=short.sample_id, provenance_id=short.provenance_id, extra=extra, raw=fragment, confidence=CONFIDENCE.HIGH, why=why)
    why += '_DEFAULT'
    return SampleID(lab_id=short.lab_id, tool_id=fix_tool_id(rn1[0]), date=fix_date(rn1[1], file_props), sample_id=short.sample_id, provenance_id=short.provenance_id, extra=extra, raw=fragment, confidence=CONFIDENCE.LOW, why=why)
  if len(rn1) == 3 and short:
    why += '_3S'
    # Expected short form: BBB_YYYYMMDD_C
    if 0 in p_tool_id and 1 in p_date and 2 in p_alphanum:
      why += '1'
      return SampleID(lab_id=short.lab_id, tool_id=fix_tool_id(rn1[0]), date=fix_date(rn1[1], file_props), sample_id=fix_alphanum(rn1[2]), provenance_id=short.provenance_id, extra=extra, raw=fragment, confidence=CONFIDENCE.HIGH, why=why)
    if len(p_tool_id) == 1 and len(p_date) == 1 and len(p_alphanum) == 1 and len(set(p_tool_id+p_date+p_alphanum)) == 3:
      why += '2'
      return SampleID(lab_id=short.lab_id, tool_id=fix_tool_id(rn1[p_tool_id[0]]), date=fix_date(rn1[p_date[0]], file_props), sample_id=fix_alphanum(rn1[p_alphanum[0]]), provenance_id=short.provenance_id, extra=extra, raw=fragment, confidence=CONFIDENCE.HIGH, why=why)
    if 1 in p_date:
      why += '3'
      # assume middle entry is date
      p_alphanum_sub = list(set(p_alphanum) - {1})
      p_tool_id_sub = list(set(p_tool_id) - {1})
      if len(p_alphanum_sub) == 1:
        why += 'A'
        tid = list({0,2} - {p_alphanum_sub[0]})[0]
        return SampleID(lab_id=short.lab_id, tool_id=fix_tool_id(rn1[tid]), date=fix_date(rn1[1], file_props), sample_id=fix_alphanum(rn1[p_alphanum_sub[0]]), provenance_id=short.provenance_id, raw=fragment, extra=extra, confidence=CONFIDENCE.MEDIUM, why=why)
      if len(p_tool_id_sub) == 1:
        why += 'B'
        nid = list({0,2} - {p_tool_id_sub[0]})[0]
        return SampleID(lab_id=short.lab_id, tool_id=fix_tool_id(rn1[p_tool_id_sub[0]]), date=fix_date(rn1[1], file_props), sample_id=fix_alphanum(rn1[nid]), provenance_id=short.provenance_id, raw=fragment, extra=extra, confidence=CONFIDENCE.MEDIUM, why=why)
    # Otherwise, assume natural order even though we didn't identify all pieces (we don't have a lab ID for rejection purposes)
    why += '_DEFAULT'
    return SampleID(lab_id=short.lab_id, tool_id=fix_tool_id(rn1[0]), date=fix_date(rn1[1], file_props), sample_id=fix_alphanum(rn1[2]), provenance_id=short.provenance_id, extra=extra, raw=fragment, confidence=CONFIDENCE.LOW, why=why)
  elif len(rn1) == 4 and short:
    why += '_4S'
    # Expected short form: BBB_YYYYMMDD_C_III *or* AAA_BBB_YYYYMMDD_C *or* BBB_YYYYMMDD_C_S
    if 0 in p_tool_id and 1 in p_date and 2 in p_alphanum and 3 in p_prov_id:
      why += '01'
      return SampleID(lab_id=short.lab_id, tool_id=fix_tool_id(rn1[0]), date=fix_date(rn1[1], file_props), sample_id=fix_alphanum(rn1[2]), provenance_id=fix_provenance_id(rn1[3]), extra=extra, raw=fragment, confidence=CONFIDENCE.HIGH, why=why)
    if 0 in p_lab_id and 1 in p_tool_id and 2 in p_date and 3 in p_alphanum:
      why += '02'
      return SampleID(lab_id=fix_lab_id(rn1[0]), tool_id=fix_tool_id(rn1[1]), date=fix_date(rn1[2], file_props), sample_id=fix_alphanum(rn1[3]), provenance_id=short.provenance_id, extra=extra, raw=fragment, confidence=CONFIDENCE.HIGH, why=why)
    if 0 in p_tool_id and 1 in p_date and 2 in p_alphanum and 3 in p_alphanum:
      why += '03'
      return SampleID(lab_id=short.lab_id, tool_id=fix_tool_id(rn1[0]), date=fix_date(rn1[1], file_props), sample_id=fix_alphanum(rn1[2]), split_id=fix_alphanum(rn1[3]), provenance_id=short.provenance_id, extra=extra, raw=fragment, confidence=CONFIDENCE.HIGH, why=why)
    if 0 in p_tool_id and 1 in p_date and 2 in p_tool_id and 3 in p_date:
      # Improper double form (see short length 2 handler above)
      return SampleID(lab_id=short.lab_id, tool_id=fix_tool_id(rn1[0]), date=fix_date(rn1[1], file_props), sample_id=short.sample_id, provenance_id=short.provenance_id, extra=extra, raw=fragment, confidence=CONFIDENCE.MEDIUM, why=why)
    if len(p_tool_id) == 1 and len(p_date) == 1 and len(p_alphanum) == 1 and len(p_prov_id) == 1 and len(set(p_tool_id+p_date+p_alphanum+p_prov_id)) == 4:
      why += '04'
      return SampleID(lab_id=short.lab_id, tool_id=fix_tool_id(rn1[p_tool_id[0]]), date=fix_date(rn1[p_date[0]], file_props), sample_id=fix_alphanum(rn1[p_alphanum[0]]), provenance_id=fix_provenance_id(rn1[p_prov_id[0]]), extra=extra, raw=fragment, confidence=CONFIDENCE.HIGH, why=why)
    if len(p_lab_id) == 1 and len(p_tool_id) == 1 and len(p_date) == 1 and len(p_alphanum) == 1 and len(set(p_lab_id+p_tool_id+p_date+p_alphanum)) == 4:
      why += '05'
      return SampleID(lab_id=fix_lab_id(rn1[p_lab_id[0]]), tool_id=fix_tool_id(rn1[p_tool_id[0]]), date=fix_date(rn1[p_date[0]], file_props), sample_id=fix_alphanum(rn1[p_alphanum[0]]), provenance_id=short.provenance_id, extra=extra, raw=fragment, confidence=CONFIDENCE.HIGH, why=why)
    if len(p_tool_id) == 1 and len(p_date) == 1 and len(p_alphanum) == 2 and len(set(p_tool_id+p_date+p_alphanum)) == 4:
      why += '06'
      return SampleID(lab_id=short.lab_id, tool_id=fix_tool_id(rn1[p_tool_id[0]]), date=fix_date(rn1[p_date[0]], file_props), sample_id=fix_alphanum(rn1[p_alphanum[0]]), split_id=fix_alphanum(rn1[p_alphanum[1]]), provenance_id=short.provenance_id, extra=extra, raw=fragment, confidence=CONFIDENCE.HIGH, why=why)
    if 0 in p_tool_id and 1 in p_date and 2 in p_alphanum and 3 in p_alphanum:
      why += '07'
      return SampleID(lab_id=short.lab_id, tool_id=fix_tool_id(rn1[0]), date=fix_date(rn1[1], file_props), sample_id=fix_alphanum(rn1[2]), split_id=fix_alphanum(rn1[3]), provenance_id=short.provenance_id, extra=extra, raw=fragment, confidence=CONFIDENCE.MEDIUM, why=why)
    if 0 in p_tool_id and 1 in p_date and 2 in p_alphanum and 3 in p_prov_id:
      why += '08'
      return SampleID(lab_id=short.lab_id, tool_id=fix_tool_id(rn1[0]), date=fix_date(rn1[1], file_props), sample_id=fix_alphanum(rn1[2]), provenance_id=fix_provenance_id(rn1[3]), extra=extra, raw=fragment, confidence=CONFIDENCE.MEDIUM, why=why)
    if 0 in p_lab_id and 1 in p_tool_id and 2 in p_date and 3 in p_alphanum:
      why += '09'
      return SampleID(lab_id=fix_lab_id(rn1[0]), tool_id=fix_tool_id(rn1[1]), date=fix_date(rn1[2], file_props), sample_id=fix_alphanum(rn1[3]), provenance_id=short.provenance_id, extra=extra, raw=fragment, confidence=CONFIDENCE.MEDIUM, why=why)
    if 2 in p_date and 0 in p_lab_id:
      why += '_DEFAULT3'
      # Assume third form even though we didn't identify all pieces.
      return SampleID(lab_id=fix_lab_id(rn1[0]), tool_id=fix_tool_id(rn1[1]), date=fix_date(rn1[2], file_props), sample_id=fix_alphanum(rn1[3]), provenance_id=short.provenance_id, extra=extra, raw=fragment, confidence=CONFIDENCE.LOW, why=why)
    if 1 in p_date and 3 in p_prov_id:
      # Assume second form even though we didn't identify all pieces (we don't have a lab ID for rejection purposes).
      why += '_DEFAULT2'
      return SampleID(lab_id=short.lab_id, tool_id=fix_tool_id(rn1[0]), date=fix_date(rn1[1], file_props), sample_id=fix_alphanum(rn1[2]), provenance_id=fix_provenance_id(rn1[3]), extra=extra, raw=fragment, confidence=CONFIDENCE.LOW, why=why)
    # Otherwise, assume first form even though we didn't identify all pieces (we don't have a lab ID for rejection purposes)
    why += '_DEFAULT'
    return SampleID(lab_id=short.lab_id, tool_id=fix_tool_id(rn1[0]), date=fix_date(rn1[1], file_props), sample_id=fix_alphanum(rn1[2]), split_id=fix_alphanum(rn1[3]), provenance_id=short.provenance_id, extra=extra, raw=fragment, confidence=CONFIDENCE.LOW, why=why)
  elif len(rn1) == 5 and short:
    why += '_5S'
    # Expected short form: AAA_BBB_YYYYMMDD_C_III or AAA_BBB_YYYYMMDD_C_S
    if 0 in p_lab_id and 1 in p_tool_id and 2 in p_date and 3 in p_alphanum and 4 in p_prov_id:
      why += '1'
      return SampleID(lab_id=fix_lab_id(rn1[0]), tool_id=fix_tool_id(rn1[1]), date=fix_date(rn1[2], file_props), sample_id=fix_alphanum(rn1[3]), provenance_id=fix_provenance_id(rn1[4]), extra=extra, raw=fragment, confidence=CONFIDENCE.HIGH, why=why)
    if 0 in p_lab_id and 1 in p_tool_id and 2 in p_date and 3 in p_alphanum and 4 in p_alphanum:
      why += '2'
      return SampleID(lab_id=fix_lab_id(rn1[0]), tool_id=fix_tool_id(rn1[1]), date=fix_date(rn1[2], file_props), sample_id=fix_alphanum(rn1[3]), split_id=fix_alphanum(rn1[4]), provenance_id=short.provenance_id, extra=extra, raw=fragment, confidence=CONFIDENCE.HIGH, why=why)
    if len(p_lab_id) == 1 and len(p_tool_id) == 1 and len(p_date) == 1 and len(p_alphanum) == 1 and len(p_prov_id) == 1 and len(set(p_lab_id+p_tool_id+p_date+p_alphanum+p_prov_id)) == 5:
      why += '3'
      return SampleID(lab_id=fix_lab_id(rn1[p_lab_id[0]]), tool_id=fix_tool_id(rn1[p_tool_id[0]]), date=fix_date(rn1[p_date[0]], file_props), sample_id=fix_alphanum(rn1[p_alphanum[0]]), provenance_id=fix_provenance_id(rn1[p_prov_id[0]]), extra=extra, raw=fragment, confidence=CONFIDENCE.HIGH, why=why)
    if len(p_lab_id) == 1 and len(p_tool_id) == 1 and len(p_date) == 1 and len(p_alphanum) == 2 and len(set(p_lab_id+p_tool_id+p_date+p_alphanum)) == 5:
      why += '4'
      return SampleID(lab_id=fix_lab_id(rn1[p_lab_id[0]]), tool_id=fix_tool_id(rn1[p_tool_id[0]]), date=fix_date(rn1[p_date[0]], file_props), sample_id=fix_alphanum(rn1[p_alphanum[0]]), split_id=fix_alphanum(rn1[p_alphanum[1]]), provenance_id=short.provenance_id, extra=extra, raw=fragment, confidence=CONFIDENCE.HIGH, why=why)
    if 0 in p_lab_id and 1 in p_tool_id and 2 in p_date and 3 in p_alphanum:
      why += '5'
      if 4 in p_prov_id:
        why += 'A'
        return SampleID(lab_id=fix_lab_id(rn1[0]), tool_id=fix_tool_id(rn1[1]), date=fix_date(rn1[2], file_props), sample_id=fix_alphanum(rn1[3]), provenance_id=fix_provenance_id(rn1[4]), extra=extra, raw=fragment, confidence=CONFIDENCE.MEDIUM, why=why)
      if 4 in p_alphanum:
        why += 'B'
        return SampleID(lab_id=fix_lab_id(rn1[0]), tool_id=fix_tool_id(rn1[1]), date=fix_date(rn1[2], file_props), sample_id=fix_alphanum(rn1[3]), split_id=fix_alphanum(rn1[4]), provenance_id=short.provenance_id, extra=extra, raw=fragment, confidence=CONFIDENCE.MEDIUM, why=why)
    # Otherwise, assume natural order with more common form
    if 0 in p_lab_id:
      why += '_DEFAULT'
      return SampleID(lab_id=fix_lab_id(rn1[0]), tool_id=fix_tool_id(rn1[1]), date=fix_date(rn1[2], file_props), sample_id=fix_alphanum(rn1[3]), provenance_id=fix_provenance_id(rn1[4]), extra=extra, raw=fragment, confidence=CONFIDENCE.LOW, why=why)
    else:
      why += '_NOLABID'
      return SampleID(extra=extra, raw=fragment, confidence=CONFIDENCE.NONE, why=why)
  elif len(rn1) == 4:
    why += '_4L'
    # Should not happen, unless it is a truncation
    if len(p_date) == 0 and len(p_lab_id) > 0 and len(p_tool_id) > 0 and len(p_alphanum) > 0 and len(p_prov_id) > 0 and len(set(p_lab_id+p_tool_id+p_alphanum+p_prov_id)) == 4:
      why += '1'
      # Treat as AAA_BBB_C_III_extra (forgotten date)
      p_lab_id_sub = p_lab_id
      p_tool_id_sub = list(set(p_tool_id) - {p_lab_id_sub[0]})
      p_alphanum_sub = []
      p_prov_id_sub = []
      if len(p_tool_id_sub) > 0:
        why += 'a'
        p_prov_id_sub = list(set(p_prov_id) - {p_lab_id_sub[0], p_tool_id_sub[0]})
      if len(p_tool_id_sub) > 0 and len(p_prov_id_sub) > 0:
        why += 'b'
        p_alphanum_sub = list(set(p_alphanum) - {p_lab_id_sub[0], p_tool_id_sub[0], p_prov_id_sub[0]})
      if len(p_lab_id_sub) > 0 and len(p_tool_id_sub) > 0 and len(p_alphanum_sub) > 0 and len(p_prov_id_sub) > 0:
        why += 'c'
        return SampleID(lab_id=fix_lab_id(rn1[p_lab_id_sub[0]]), tool_id=fix_tool_id(rn1[p_tool_id_sub[0]]), sample_id=fix_alphanum(rn1[p_alphanum_sub[0]]), provenance_id=fix_provenance_id(rn1[p_prov_id_sub[0]]), extra=extra, raw=fragment, confidence=CONFIDENCE.MEDIUM, why=why)
    if len(p_lab_id) > 0 and len(p_date) > 0 and len(p_tool_id) > 0 and len(p_prov_id) > 0 and len(set(p_lab_id+p_date+p_tool_id+p_prov_id)) == 4:
      why += '2'
      # Treat as AAA_BBB_YYYYMMDD_III_extra (forgotten sample number)
      p_lab_id_sub = p_lab_id
      p_tool_id_sub = list(set(p_tool_id) - {p_lab_id_sub[0]})
      p_date_sub = []
      p_prov_id_sub = []
      if len(p_tool_id_sub) > 0:
        why += 'a'
        p_date_sub = list(set(p_date) - {p_lab_id_sub[0], p_tool_id_sub[0]})
      if len(p_tool_id_sub) > 0 and len(p_date_sub) > 0:
        why += 'b'
        p_prov_id_sub = list(set(p_prov_id) - {p_lab_id_sub[0], p_tool_id_sub[0], p_date_sub[0]})
      if len(p_lab_id_sub) > 0 and len(p_tool_id_sub) > 0 and len(p_date_sub) > 0 and len(p_prov_id_sub) > 0:
        why += 'c'
        return SampleID(lab_id=fix_lab_id(rn1[p_lab_id_sub[0]]), tool_id=fix_tool_id(rn1[p_tool_id_sub[0]]), date=fix_date(rn1[p_date_sub[0]], file_props), provenance_id=fix_provenance_id(rn1[p_prov_id_sub[0]]), extra=extra, raw=fragment, confidence=CONFIDENCE.MEDIUM, why=why)
    if len(p_lab_id) > 0 and len(p_date) > 0 and len(p_tool_id) == 0 and len(p_alphanum) > 0 and len(p_prov_id) > 0 and len(set(p_lab_id+p_date+p_alphanum+p_prov_id)) == 4:
      why += '3'
      # Treat as AAA_YYYYMMDD_C_III_extra (forgotten tool number)
      p_lab_id_sub = p_lab_id
      p_date_sub = list(set(p_date) - {p_lab_id_sub[0]})
      p_prov_id_sub = []
      p_alphanum_sub = []
      if len(p_date_sub) > 0:
        why += 'a'
        p_prov_id_sub = list(set(p_prov_id) - {p_lab_id_sub[0], p_date_sub[0]})
      if len(p_date_sub) > 0 and len(p_prov_id_sub) > 0:
        why += 'b'
        p_alphanum_sub = list(set(p_alphanum) - {p_lab_id_sub[0], p_date_sub[0], p_prov_id_sub[0]})
      if len(p_lab_id_sub) > 0 and len(p_alphanum_sub) > 0 and len(p_date_sub) > 0 and len(p_prov_id_sub) > 0:
        why += 'c'
        return SampleID(lab_id=fix_lab_id(rn1[p_lab_id_sub[0]]), date=fix_date(rn1[p_date_sub[0]], file_props), sample_id=fix_alphanum(rn1[p_alphanum_sub[0]]), provenance_id=fix_provenance_id(rn1[p_prov_id_sub[0]]), extra=extra, raw=fragment, confidence=CONFIDENCE.MEDIUM, why=why)
    # Otherwise, unparseable
    why += '_SHORT'
    return SampleID(extra=extra, raw=fragment, confidence=CONFIDENCE.NONE, why=why)
  elif len(rn1) == 5:
    why += '_5L'
    # Expected long form: AAA_BBB_YYYYMMDD_C_III
    if 0 in p_lab_id and 1 in p_tool_id and 2 in p_date and 3 in p_alphanum and 4 in p_prov_id:
      why += '01'
      return SampleID(lab_id=fix_lab_id(rn1[0]), tool_id=fix_tool_id(rn1[1]), date=fix_date(rn1[2], file_props), sample_id=fix_alphanum(rn1[3]), provenance_id=fix_provenance_id(rn1[4]), extra=extra, raw=fragment, confidence=CONFIDENCE.HIGH, why=why)
    if len(p_lab_id) == 1 and len(p_tool_id) == 1 and len(p_date) == 1 and len(p_alphanum) == 1 and len(p_prov_id) == 1 and len(set(p_lab_id+p_tool_id+p_date+p_alphanum+p_prov_id)) == 5:
      # Probably right, but possible that there is a missing sample_id and the alphanum is the split
      why += '02'
      return SampleID(lab_id=fix_lab_id(rn1[p_lab_id[0]]), tool_id=fix_tool_id(rn1[p_tool_id[0]]), date=fix_date(rn1[p_date[0]], file_props), sample_id=fix_alphanum(rn1[p_alphanum[0]]), provenance_id=fix_provenance_id(rn1[p_prov_id[0]]), extra=extra, raw=fragment, confidence=CONFIDENCE.MEDIUM, why=why)
    # If we recognize four of five key parts, we believe
    if 0 in p_lab_id and 1 in p_tool_id and 2 in p_date and 3 in p_alphanum:
      why += '03'
      return SampleID(lab_id=fix_lab_id(rn1[0]), tool_id=fix_tool_id(rn1[1]), date=fix_date(rn1[2], file_props), sample_id=fix_alphanum(rn1[3]), provenance_id=fix_provenance_id(rn1[4]), extra=extra, raw=fragment, confidence=CONFIDENCE.MEDIUM, why=why)
    if 0 in p_lab_id and 1 in p_tool_id and 2 in p_date and 4 in p_prov_id:
      why += '04'
      return SampleID(lab_id=fix_lab_id(rn1[0]), tool_id=fix_tool_id(rn1[1]), date=fix_date(rn1[2], file_props), sample_id=fix_alphanum(rn1[3]), provenance_id=fix_provenance_id(rn1[4]), extra=extra, raw=fragment, confidence=CONFIDENCE.MEDIUM, why=why)
    if 0 in p_lab_id and 2 in p_date and 3 in p_alphanum and 4 in p_prov_id:
      why += '05'
      return SampleID(lab_id=fix_lab_id(rn1[0]), tool_id=fix_tool_id(rn1[1]), date=fix_date(rn1[2], file_props), sample_id=fix_alphanum(rn1[3]), provenance_id=fix_provenance_id(rn1[4]), extra=extra, raw=fragment, confidence=CONFIDENCE.MEDIUM, why=why)
    if len(p_date) == 0 and len(p_lab_id) > 0 and len(p_tool_id) > 0 and len(p_alphanum) > 0 and len(p_prov_id) > 0 and len(set(p_lab_id+p_tool_id+p_alphanum+p_prov_id) - {4}) == 4:
      why += '06'
      # Treat as AAA_BBB_C_III_extra (forgotten date)
      p_lab_id_sub = p_lab_id
      p_tool_id_sub = list(set(p_tool_id) - {p_lab_id_sub[0]})
      p_alphanum_sub = []
      p_prov_id_sub = []
      if len(p_tool_id_sub) > 0:
        why += 'a'
        p_prov_id_sub = list(set(p_prov_id) - {p_lab_id_sub[0], p_tool_id_sub[0]})
      if len(p_tool_id_sub) > 0 and len(p_prov_id_sub) > 0:
        why += 'b'
        p_alphanum_sub = list(set(p_alphanum) - {p_lab_id_sub[0], p_tool_id_sub[0], p_prov_id_sub[0]})
      if len(p_lab_id_sub) > 0 and len(p_tool_id_sub) > 0 and len(p_alphanum_sub) > 0 and len(p_prov_id_sub) > 0:
        why += 'c'
        return SampleID(lab_id=fix_lab_id(rn1[p_lab_id_sub[0]]), tool_id=fix_tool_id(rn1[p_tool_id_sub[0]]), sample_id=fix_alphanum(rn1[p_alphanum_sub[0]]), provenance_id=fix_provenance_id(rn1[p_prov_id_sub[0]]), extra=rn1[4]+extra, raw=fragment, confidence=CONFIDENCE.MEDIUM, why=why)
    if len(p_lab_id) > 0 and len(p_date) > 0 and len(p_tool_id) > 0 and len(p_prov_id) > 0 and len(set(p_lab_id+p_date+p_tool_id+p_prov_id) - {4}) == 4:
      why += '07'
      # Treat as AAA_BBB_YYYYMMDD_III_extra (forgotten sample number)
      p_lab_id_sub = p_lab_id
      p_tool_id_sub = list(set(p_tool_id) - {p_lab_id_sub[0]})
      p_date_sub = []
      p_prov_id_sub = []
      if len(p_tool_id_sub) > 0:
        why += 'a'
        p_date_sub = list(set(p_date) - {p_lab_id_sub[0], p_tool_id_sub[0]})
      if len(p_tool_id_sub) > 0 and len(p_date_sub) > 0:
        why += 'b'
        p_prov_id_sub = list(set(p_prov_id) - {p_lab_id_sub[0], p_tool_id_sub[0], p_date_sub[0]})
      if len(p_lab_id_sub) > 0 and len(p_tool_id_sub) > 0 and len(p_date_sub) > 0 and len(p_prov_id_sub) > 0:
        why += 'c'
        return SampleID(lab_id=fix_lab_id(rn1[p_lab_id_sub[0]]), tool_id=fix_tool_id(rn1[p_tool_id_sub[0]]), date=fix_date(rn1[p_date_sub[0]], file_props), provenance_id=fix_provenance_id(rn1[p_prov_id_sub[0]]), extra=rn1[4]+extra, raw=fragment, confidence=CONFIDENCE.MEDIUM, why=why)
    if len(p_lab_id) > 0 and len(p_date) > 0 and len(p_tool_id) == 0 and len(p_alphanum) > 0 and len(p_prov_id) > 0 and len(set(p_lab_id+p_date+p_alphanum+p_prov_id) - {4}) == 4:
      why += '08'
      # Treat as AAA_YYYYMMDD_C_III_extra (forgotten tool number)
      p_lab_id_sub = p_lab_id
      p_date_sub = list(set(p_date) - {p_lab_id_sub[0]})
      p_prov_id_sub = []
      p_alphanum_sub = []
      if len(p_date_sub) > 0:
        why += 'a'
        p_prov_id_sub = list(set(p_prov_id) - {p_lab_id_sub[0], p_date_sub[0]})
      if len(p_date_sub) > 0 and len(p_prov_id_sub) > 0:
        why += 'b'
        p_alphanum_sub = list(set(p_alphanum) - {p_lab_id_sub[0], p_date_sub[0], p_prov_id_sub[0]})
      if len(p_lab_id_sub) > 0 and len(p_alphanum_sub) > 0 and len(p_date_sub) > 0 and len(p_prov_id_sub) > 0:
        why += 'c'
        return SampleID(lab_id=fix_lab_id(rn1[p_lab_id_sub[0]]), date=fix_date(rn1[p_date_sub[0]], file_props), sample_id=fix_alphanum(rn1[p_alphanum_sub[0]]), provenance_id=fix_provenance_id(rn1[p_prov_id_sub[0]]), extra=rn1[4]+extra, raw=fragment, confidence=CONFIDENCE.MEDIUM, why=why)
    # Otherwise, assume natural order
    if 0 in p_lab_id:
      why += '_DEFAULT'
      return SampleID(lab_id=fix_lab_id(rn1[0]), tool_id=fix_tool_id(rn1[1]), date=fix_date(rn1[2], file_props), sample_id=fix_alphanum(rn1[3]), provenance_id=fix_provenance_id(rn1[4]), extra=extra, raw=fragment, confidence=CONFIDENCE.LOW, why=why)
    else:
      why += '_NOLABID'
      return SampleID(extra=extra, raw=fragment, confidence=CONFIDENCE.NONE, why=why)
  elif len(rn1) == 6:
    why += '_6L'
    # Expected long form: AAA_BBB_YYYYMMDD_C_III_S
    if 0 in p_lab_id and 1 in p_tool_id and 2 in p_date and 3 in p_alphanum and 4 in p_prov_id and 5 in p_alphanum:
      why += '01'
      return SampleID(lab_id=fix_lab_id(rn1[0]), tool_id=fix_tool_id(rn1[1]), date=fix_date(rn1[2], file_props), sample_id=fix_alphanum(rn1[3]), provenance_id=fix_provenance_id(rn1[4]), split_id=fix_alphanum(rn1[5]), extra=extra, raw=fragment, confidence=CONFIDENCE.HIGH, why=why)
    if len(p_lab_id) == 1 and len(p_tool_id) == 1 and len(p_date) == 1 and len(p_alphanum) == 2 and len(p_prov_id) == 1:
      why += '02'
      return SampleID(lab_id=fix_lab_id(rn1[p_lab_id[0]]), tool_id=fix_tool_id(rn1[p_tool_id[0]]), date=fix_date(rn1[p_date[0]], file_props), sample_id=fix_alphanum(rn1[p_alphanum[0]]), provenance_id=fix_provenance_id(rn1[p_prov_id[0]]), split_id=fix_alphanum(rn1[p_alphanum[1]]), extra=extra, raw=fragment, confidence=CONFIDENCE.HIGH, why=why)
    # If we recognize five of the six, we believe
    if 0 in p_lab_id and 1 in p_tool_id and 2 in p_date and 3 in p_alphanum and 4 in p_prov_id:
      why += '03'
      return SampleID(lab_id=fix_lab_id(rn1[0]), tool_id=fix_tool_id(rn1[1]), date=fix_date(rn1[2], file_props), sample_id=fix_alphanum(rn1[3]), provenance_id=fix_provenance_id(rn1[4]), split_id=fix_alphanum(rn1[5]), extra=extra, raw=fragment, confidence=CONFIDENCE.MEDIUM, why=why)
    if 0 in p_lab_id and 1 in p_tool_id and 2 in p_date and 3 in p_alphanum and 5 in p_alphanum:
      why += '04'
      return SampleID(lab_id=fix_lab_id(rn1[0]), tool_id=fix_tool_id(rn1[1]), date=fix_date(rn1[2], file_props), sample_id=fix_alphanum(rn1[3]), provenance_id=fix_provenance_id(rn1[4]), split_id=fix_alphanum(rn1[5]), extra=extra, raw=fragment, confidence=CONFIDENCE.MEDIUM, why=why)
    if 0 in p_lab_id and 1 in p_tool_id and 2 in p_date and 4 in p_prov_id and 5 in p_alphanum:
      why += '05'
      return SampleID(lab_id=fix_lab_id(rn1[0]), tool_id=fix_tool_id(rn1[1]), date=fix_date(rn1[2], file_props), sample_id=fix_alphanum(rn1[3]), provenance_id=fix_provenance_id(rn1[4]), split_id=fix_alphanum(rn1[5]), extra=extra, raw=fragment, confidence=CONFIDENCE.MEDIUM, why=why)
    if 0 in p_lab_id and 2 in p_date and 3 in p_alphanum and 4 in p_prov_id and 5 in p_alphanum:
      why += '06'
      return SampleID(lab_id=fix_lab_id(rn1[0]), tool_id=fix_tool_id(rn1[1]), date=fix_date(rn1[2], file_props), sample_id=fix_alphanum(rn1[3]), provenance_id=fix_provenance_id(rn1[4]), split_id=fix_alphanum(rn1[5]), extra=extra, raw=fragment, confidence=CONFIDENCE.MEDIUM, why=why)
    if len(p_date) == 0 and len(p_lab_id) > 0 and len(p_tool_id) > 0 and len(p_alphanum) > 1 and len(p_prov_id) > 0 and len(set(p_lab_id+p_tool_id+p_alphanum+p_prov_id) - {5}) == 5:
      why += '07'
      # Treat as AAA_BBB_C_III_S_extra (forgotten date)
      p_lab_id_sub = p_lab_id
      p_tool_id_sub = list(set(p_tool_id) - {p_lab_id_sub[0]})
      p_alphanum_sub = []
      p_prov_id_sub = []
      if len(p_tool_id_sub) > 0:
        why += 'a'
        p_prov_id_sub = list(set(p_prov_id) - {p_lab_id_sub[0], p_tool_id_sub[0]})
      if len(p_tool_id_sub) > 0 and len(p_prov_id_sub) > 0:
        why += 'b'
        p_alphanum_sub = list(set(p_alphanum) - {p_lab_id_sub[0], p_tool_id_sub[0], p_prov_id_sub[0]})
      if len(p_lab_id_sub) > 0 and len(p_tool_id_sub) > 0 and len(p_alphanum_sub) > 1 and len(p_prov_id_sub) > 0:
        why += 'c'
        return SampleID(lab_id=fix_lab_id(rn1[p_lab_id_sub[0]]), tool_id=fix_tool_id(rn1[p_tool_id_sub[0]]), sample_id=fix_alphanum(rn1[p_alphanum_sub[0]]), provenance_id=fix_provenance_id(rn1[p_prov_id_sub[0]]), split_id=fix_alphanum(rn1[p_alphanum_sub[1]]), extra=rn1[5]+extra, raw=fragment, confidence=CONFIDENCE.MEDIUM, why=why)
    if len(p_lab_id) > 0 and len(p_date) > 0 and len(p_tool_id) > 0 and len(p_prov_id) > 0 and len(p_alphanum) > 0 and len(set(p_lab_id+p_date+p_tool_id+p_prov_id+p_alphanum) - {5}) == 5:
      why += '08'
      # Treat as AAA_BBB_YYYYMMDD_C_III_extra (forgotten split or sample ID, which are indistinguishable)
      p_lab_id_sub = p_lab_id
      p_tool_id_sub = list(set(p_tool_id) - {p_lab_id_sub[0]})
      p_date_sub = []
      p_prov_id_sub = []
      p_alphanum_sub = []
      if len(p_tool_id_sub) > 0:
        why += 'a'
        p_date_sub = list(set(p_date) - {p_lab_id_sub[0], p_tool_id_sub[0]})
      if len(p_tool_id_sub) > 0 and len(p_date_sub) > 0:
        why += 'b'
        p_prov_id_sub = list(set(p_prov_id) - {p_lab_id_sub[0], p_tool_id_sub[0], p_date_sub[0]})
      if len(p_tool_id_sub) > 0 and len(p_date_sub) > 0 and len(p_prov_id_sub) > 0:
        why += 'c'
        p_alphanum_sub = list(set(p_alphanum) - {p_lab_id_sub[0], p_tool_id_sub[0], p_date_sub[0], p_prov_id_sub[0]})
      if len(p_lab_id_sub) > 0 and len(p_tool_id_sub) > 0 and len(p_date_sub) > 0 and len(p_prov_id_sub) > 0 and len(p_alphanum_sub) > 0:
        why += 'd'
        return SampleID(lab_id=fix_lab_id(rn1[p_lab_id_sub[0]]), tool_id=fix_tool_id(rn1[p_tool_id_sub[0]]), date=fix_date(rn1[p_date_sub[0]], file_props), sample_id=fix_alphanum(rn1[p_alphanum_sub[0]]), provenance_id=fix_provenance_id(rn1[p_prov_id_sub[0]]), extra=rn1[5]+extra, raw=fragment, confidence=CONFIDENCE.MEDIUM, why=why)
    # Otherwise, assume natural order
    if 0 in p_lab_id:
      why += '_DEFAULT'
      return SampleID(lab_id=fix_lab_id(rn1[0]), tool_id=fix_tool_id(rn1[1]), date=fix_date(rn1[2], file_props), sample_id=fix_alphanum(rn1[3]), provenance_id=fix_provenance_id(rn1[4]), split_id=fix_alphanum(rn1[5]), extra=extra, raw=fragment, confidence=CONFIDENCE.LOW, why=why)
    else:
      why += '_NOLABID'
      return SampleID(extra=extra, raw=fragment, confidence=CONFIDENCE.NONE, why=why)
  elif len(p_lab_id) > 0 and len(p_prov_id) > 0:
    why += '_LABPROVONLY'
    return SampleID(lab_id=fix_lab_id(rn1[p_lab_id[0]]), provenance_id=fix_provenance_id(rn1[p_prov_id[0]]), extra=extra, raw=fragment, confidence=CONFIDENCE.LOW, why=why)
  else:
    why += '_NOPARSE'
    return SampleID(extra=extra, raw=fragment, confidence=CONFIDENCE.NONE, why=why)

def replace(s, patt, repl, ignorecase=True):
  c = re.compile(re.escape(patt), re.IGNORECASE) if ignorecase else re.compile(re.escape(patt))
  return c.sub(repl, s)

def parse(raw_name, lab_ids, tool_ids, prov_ids, fixups={}, file_props=None):
  why = 'P'
  # 0. Name fixups
  name = raw_name
  for fu in fixups:
    name = replace(name, fu, fixups[fu])
  # 1. Get regular name part
  rn1 = name.split('-')
  follow = "".join(rn1[1:])
  rn1 = rn1[0]
  # 2. Split off parent samples
  rn2 = rn1.split('_(')
  # 3. All parts except the first should end in )
  rn3 = [rn2[0]]
  for i in range(1,len(rn2)):
    why += '_PARENT' + str(i)
    n = rn2[i]
    if not n.endswith(')'):
      why = '_MISSINGPAREN'
      # treat everything from here to end of line as extra since there is no closing parens
      follow = "".join(["_(", "_(".join(rn2[i:]), follow])
      break
    rn3.append(n.strip(')'))
  # 4. Process main fragment, then parents
  mf = parse_internal(rn3[0], lab_ids, tool_ids, prov_ids, file_props=file_props, why=why, short=False)
  pfs = []
  for i in range(1,len(rn3)):
    pfs.append(parse_internal(rn3[i], lab_ids, tool_ids, prov_ids, file_props=file_props, why=mf.why, short=mf))
  # 5. Reassemble final main tuple
  return SampleID(lab_id=mf.lab_id, tool_id=mf.tool_id, date=mf.date, sample_id=mf.sample_id, provenance_id=mf.provenance_id, split_id=mf.split_id, parents=pfs, extra=mf.extra+follow, raw=name, confidence=mf.confidence, why=mf.why)
