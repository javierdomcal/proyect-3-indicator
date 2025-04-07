%chk=942781.chk
%mem=4GB
%NProcShared=1
#P SP CASSCF(2,2)/TZVP gfinput fchk=all density=current iop(5/33=1) out=wfx

942781 hydrogen_2eq CASSCF(2,2) TZVP

0 1
H    0.000000   0.000000  -0.750000
H    0.000000   0.000000   0.750000

942781.wfx

