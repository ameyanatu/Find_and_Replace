*** Settings ***
Library  Find_And_Replace.py

*** Test Cases ***
Testing Find and Replace
    find and replace keyword from single text file  test.txt  Bikram  Ameya
    find and replace keyword from multiple text file  E://RobotFrameworkProjects//Find-and-Replace//sample_textfiles  Natu  Gopal
    find and replace keyword from single CSV file  Test_CSV.csv  Ameya  Pooja
    find and replace keyword from multiple CSV file  E://RobotFrameworkProjects//Find-and-Replace//sample_csvfiles  School  Ameya