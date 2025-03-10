%chk=CALC_000059.chk
%mem=4GB
%NProcShared=1
#P SP CISD/cc-pVTZ gfinput fchk=all density=rhoci iop(9/40=7) iop(9/28=-1) use=l916 out=wfx

CALC_000059 neon CISD cc-pVTZ

0 1
Ne 0.0 0.0 0.0

CALC_000059.wfx

