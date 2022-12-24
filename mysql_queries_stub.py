import mysql.connector

mydb = mysql.connector.connect(
    host = "localhost",
    username = "root",
    password = "",
    database="bucit"
)
mycursor = mydb.cursor()
mycursor.execute("CREATE TABLE customers (name VARCHAR(255), address VARCHAR(255))")
print("done")




"""
CREATE TABLE `transcripts` (
`ensembl_transcript_id` varchar(20) NOT NULL,
`transcript_chrom_start` int(10) unsigned NOT NULL,
`transcript_chrom_end` int(10) unsigned NOT NULL,
PRIMARY KEY (`ensembl_transcript_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

"""

"""
REPLACE INTO `transcripts`
SET `ensembl_transcript_id` = 'ENSORGT00000000001',
`transcript_chrom_start` = 12345,
`transcript_chrom_end` = 12678;
"""

"""INSERT IGNORE INTO `transcripts`
SET `ensembl_transcript_id` = 'ENSORGT00000000001',
`transcript_chrom_start` = 12345,
`transcript_chrom_end` = 12678;"""


