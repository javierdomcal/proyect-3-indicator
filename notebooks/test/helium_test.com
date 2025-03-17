%chk=helium_test.chk
%mem=4GB
%NProcShared=1
#P SP CASSCF(2,2)/6-31G gfinput fchk=all density=current iop(5/33=1) out=wfx

helium_test helium CASSCF(2,2) 6-31G

0 1
He    0.0000   0.0000   0.0000

helium_test.wfx
