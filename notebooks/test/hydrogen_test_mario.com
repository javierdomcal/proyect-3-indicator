%chk=hydrogen_test_mario.chk
%mem=4GB
%NProcShared=1
#P Opt CASSCF(2,2)/6-31G gfinput fchk=all density=current iop(5/33=1) out=wfx

hydrogen_test_mario hydrogen CASSCF(2,2) 6-31G

0 1
H    0.0000   0.0000   0.0000
H    0.7400   0.0000   0.0000

hydrogen_test_mario.wfx
