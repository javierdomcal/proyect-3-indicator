%chk=helium_tyring_test.chk
%mem=4GB
%NProcShared=4
#P SP CISD/sto-3g gfinput fchk=all density=rhoci iop(9/40=7) iop(9/28=-1) use=l916 out=wfx

helium_tyring_test helium CISD sto-3g

0 1
He    0.0000   0.0000   0.0000

helium_tyring_test.wfx
