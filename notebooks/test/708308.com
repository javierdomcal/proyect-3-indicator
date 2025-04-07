%chk=708308.chk
%mem=4GB
%NProcShared=1
#P SP CASSCF(2,2)/TZVP gfinput fchk=all density=current iop(5/33=1) out=wfx

708308 hydrogen_5eq CASSCF(2,2) TZVP

0 1
H    0.000000   0.000000  -1.850000
H    0.000000   0.000000   1.850000

708308.wfx

