%chk=gaussian_test.chk
%mem=4GB
%NProcShared=1
#P SP CISD/sto-3g gfinput fchk=all density=rhoci iop(9/40=7) iop(9/28=-1) use=l916 out=wfx

gaussian_test hydrogen_atom CISD sto-3g

0 2
H    0.0000   0.0000   0.0000

gaussian_test.wfx
