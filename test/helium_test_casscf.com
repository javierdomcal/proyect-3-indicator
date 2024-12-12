%chk=helium_test_casscf.chk
%mem=2GB
%NProcShared=1
#P SP CASSCF(2,2)/6-31G density=current gfinput fchk=all out=wfx iop(9/40=7) iop(9/28=-1) use=l916

helium_test_casscf helium CASSCF(2,2) 6-31G

0 1
He    0.0000   0.0000   0.0000

helium_test_casscf.wfx

