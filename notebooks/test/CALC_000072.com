%chk=CALC_000072.chk
%mem=4GB
%NProcShared=1
#P SP HF/aug-cc-pVDZ gfinput fchk=all out=wfx

CALC_000072 hydrogen_5eq HF aug-cc-pVDZ

0 1
H    0.000000   0.000000  -1.850000
H    0.000000   0.000000   1.850000

CALC_000072.wfx

