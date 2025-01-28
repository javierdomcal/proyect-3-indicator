%chk=test_gaussian.chk
%mem=4GB
%NProcShared=1
#P SP HF/sto-3g gfinput fchk=all density=rhoci iop(9/40=7) iop(9/28=-1) use=l916 out=wfx

test_gaussian water HF sto-3g

0 1
O 0.0 0.0 0.0
H 0.0 0.0 0.96
H 0.0 0.75 -0.36

test_gaussian.wfx
