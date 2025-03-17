%chk=CALC_000016.chk
%mem=4GB
%NProcShared=1
#P SP CISD/cc-pVDZ gfinput fchk=all density=rhoci iop(9/40=7) iop(9/28=-1) use=l916 out=wfx

CALC_000016 helium CISD cc-pVDZ

0 1
He    0.0000   0.0000   0.0000

CALC_000016.wfx

