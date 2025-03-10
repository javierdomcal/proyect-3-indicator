%chk=CALC_000017.chk
%mem=4GB
%NProcShared=1
#P SP CISD/aug-cc-pVDZ gfinput fchk=all density=rhoci iop(9/40=7) iop(9/28=-1) use=l916 out=wfx

CALC_000017 helium CISD aug-cc-pVDZ

0 1
He    0.0000   0.0000   0.0000

CALC_000017.wfx

