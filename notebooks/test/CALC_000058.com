%chk=CALC_000058.chk
%mem=4GB
%NProcShared=1
#P SP CISD/aug-cc-pVDZ gfinput fchk=all density=rhoci iop(9/40=7) iop(9/28=-1) use=l916 out=wfx

CALC_000058 neon CISD aug-cc-pVDZ

0 1
Ne 0.0 0.0 0.0

CALC_000058.wfx

